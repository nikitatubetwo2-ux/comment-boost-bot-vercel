import type { Handler } from '@netlify/functions'
import * as storage from '../../lib/storage'
import { getLatestVideos, getVideoDetails } from '../../lib/youtube'
import { generateComments } from '../../lib/comments'
import { sendVideoNotification } from '../../lib/telegram'

export const handler: Handler = async (event) => {
  // Simple auth check
  const authHeader = event.headers.authorization
  const expectedToken = process.env.CRON_SECRET || 'cron123'
  
  if (authHeader !== `Bearer ${expectedToken}`) {
    return { statusCode: 401, body: JSON.stringify({ error: 'Unauthorized' }) }
  }
  
  console.log('[Cron] Starting video check...')
  
  try {
    const channels = await storage.getAllChannels()
    console.log(`[Cron] Checking ${channels.length} channels`)
    
    let newVideosFound = 0
    
    for (const channel of channels) {
      try {
        const videos = await getLatestVideos(channel.youtubeId, 3)
        
        for (const video of videos) {
          const videoAge = Date.now() - video.publishedAt.getTime()
          const twoHours = 2 * 60 * 60 * 1000
          
          if (videoAge > twoHours) continue
          
          const isProcessed = await storage.isVideoProcessed(video.id)
          if (isProcessed) continue
          
          console.log(`[Cron] New video found: ${video.title}`)
          
          const details = await getVideoDetails(video.id)
          if (!details) continue
          
          const comments = await generateComments({
            title: details.title,
            description: details.description,
            tags: details.tags,
            channelName: channel.name,
            language: details.defaultLanguage || 'en',
          })
          
          const profile = await storage.getProfileById(channel.profileId)
          if (profile) {
            await sendVideoNotification(profile.userId, {
              title: details.title,
              channelName: channel.name,
              thumbnailUrl: details.thumbnailUrl,
              videoId: video.id,
            }, comments)
          }
          
          await storage.markVideoProcessed(video.id)
          newVideosFound++
        }
      } catch (error) {
        console.error(`[Cron] Error checking channel ${channel.name}:`, error)
      }
    }
    
    console.log(`[Cron] Done. Found ${newVideosFound} new videos.`)
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        ok: true,
        channelsChecked: channels.length,
        newVideosFound,
      })
    }
  } catch (error) {
    console.error('[Cron] Error:', error)
    return { statusCode: 500, body: JSON.stringify({ error: 'Internal error' }) }
  }
}
