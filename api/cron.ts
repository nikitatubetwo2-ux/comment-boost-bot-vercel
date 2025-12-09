import type { VercelRequest, VercelResponse } from '@vercel/node'
import * as storage from '../lib/storage'
import { getLatestVideos, getVideoDetails } from '../lib/youtube'
import { generateComments } from '../lib/comments'
import { sendVideoNotification } from '../lib/telegram'

// This endpoint is called by external cron service (cron-job.org)
// every 15 minutes to check for new videos

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Simple auth check
  const authHeader = req.headers.authorization
  const expectedToken = process.env.CRON_SECRET || 'cron123'
  
  if (authHeader !== `Bearer ${expectedToken}`) {
    return res.status(401).json({ error: 'Unauthorized' })
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
          // Check if video is new (less than 2 hours old)
          const videoAge = Date.now() - video.publishedAt.getTime()
          const twoHours = 2 * 60 * 60 * 1000
          
          if (videoAge > twoHours) continue
          
          // Check if already processed
          const isProcessed = await storage.isVideoProcessed(video.id)
          if (isProcessed) continue
          
          console.log(`[Cron] New video found: ${video.title}`)
          
          // Get full video details
          const details = await getVideoDetails(video.id)
          if (!details) continue
          
          // Generate comments
          const comments = await generateComments({
            title: details.title,
            description: details.description,
            tags: details.tags,
            channelName: channel.name,
            language: details.defaultLanguage?.startsWith('ru') ? 'ru' : 'en',
          })
          
          // Find all users who track this channel and notify them
          const profile = await storage.getProfileById(channel.profileId)
          if (profile) {
            await sendVideoNotification(profile.userId, {
              title: details.title,
              channelName: channel.name,
              thumbnailUrl: details.thumbnailUrl,
              videoId: video.id,
            }, comments)
          }
          
          // Mark as processed
          await storage.markVideoProcessed(video.id)
          newVideosFound++
        }
      } catch (error) {
        console.error(`[Cron] Error checking channel ${channel.name}:`, error)
      }
    }
    
    console.log(`[Cron] Done. Found ${newVideosFound} new videos.`)
    
    res.status(200).json({
      ok: true,
      channelsChecked: channels.length,
      newVideosFound,
    })
  } catch (error) {
    console.error('[Cron] Error:', error)
    res.status(500).json({ error: 'Internal error' })
  }
}
