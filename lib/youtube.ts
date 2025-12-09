import { google, youtube_v3 } from 'googleapis'
import { config } from './config'

let currentKeyIndex = 0
const failedKeys = new Set<string>()

function getYouTubeClient(): youtube_v3.Youtube {
  const keys = config.youtube.apiKeys.filter(k => !failedKeys.has(k))
  if (keys.length === 0) {
    throw new Error('All YouTube API keys exhausted')
  }
  currentKeyIndex = currentKeyIndex % keys.length
  return google.youtube({ version: 'v3', auth: keys[currentKeyIndex] })
}

function rotateKey(): void {
  const key = config.youtube.apiKeys[currentKeyIndex]
  failedKeys.add(key)
  currentKeyIndex = (currentKeyIndex + 1) % config.youtube.apiKeys.length
}

async function withRetry<T>(fn: (yt: youtube_v3.Youtube) => Promise<T>): Promise<T> {
  for (let i = 0; i < config.youtube.apiKeys.length; i++) {
    try {
      return await fn(getYouTubeClient())
    } catch (error: unknown) {
      const err = error as { code?: number; message?: string }
      if (err.code === 403 && err.message?.includes('quota')) {
        rotateKey()
        continue
      }
      throw error
    }
  }
  throw new Error('All YouTube API keys exhausted')
}

export async function getLatestVideos(channelId: string, maxResults = 5) {
  return withRetry(async (youtube) => {
    const response = await youtube.search.list({
      part: ['snippet'],
      channelId,
      order: 'date',
      type: ['video'],
      maxResults,
    })

    return (response.data.items || []).map(item => ({
      id: item.id?.videoId || '',
      channelId,
      title: item.snippet?.title || '',
      description: item.snippet?.description || '',
      thumbnailUrl: item.snippet?.thumbnails?.high?.url || '',
      publishedAt: new Date(item.snippet?.publishedAt || Date.now()),
    }))
  })
}

export async function getVideoDetails(videoId: string) {
  return withRetry(async (youtube) => {
    const response = await youtube.videos.list({
      part: ['snippet', 'statistics'],
      id: [videoId],
    })

    const video = response.data.items?.[0]
    if (!video) return null

    return {
      id: video.id || '',
      channelId: video.snippet?.channelId || '',
      title: video.snippet?.title || '',
      description: video.snippet?.description || '',
      thumbnailUrl: video.snippet?.thumbnails?.high?.url || '',
      publishedAt: new Date(video.snippet?.publishedAt || Date.now()),
      tags: video.snippet?.tags || [],
      viewCount: parseInt(video.statistics?.viewCount || '0', 10),
      likeCount: parseInt(video.statistics?.likeCount || '0', 10),
      commentCount: parseInt(video.statistics?.commentCount || '0', 10),
      defaultLanguage: video.snippet?.defaultLanguage || video.snippet?.defaultAudioLanguage || 'en',
    }
  })
}

export async function validateChannel(input: string) {
  // Parse channel URL/ID
  const channelUrlMatch = input.match(/youtube\.com\/channel\/([a-zA-Z0-9_-]+)/)
  const handleUrlMatch = input.match(/youtube\.com\/@([a-zA-Z0-9_.-]+)/)
  
  let searchQuery = input
  if (channelUrlMatch) {
    // Direct ID lookup
    return withRetry(async (youtube) => {
      const response = await youtube.channels.list({
        part: ['snippet'],
        id: [channelUrlMatch[1]],
      })
      const channel = response.data.items?.[0]
      if (channel) {
        return { isValid: true, channelId: channel.id!, channelName: channel.snippet?.title }
      }
      return { isValid: false, error: 'Channel not found' }
    })
  }
  
  if (handleUrlMatch) {
    searchQuery = handleUrlMatch[1]
  } else if (input.startsWith('@')) {
    searchQuery = input.slice(1)
  }

  return withRetry(async (youtube) => {
    const response = await youtube.search.list({
      part: ['snippet'],
      q: searchQuery,
      type: ['channel'],
      maxResults: 1,
    })
    const channel = response.data.items?.[0]
    if (channel) {
      return { isValid: true, channelId: channel.snippet?.channelId!, channelName: channel.snippet?.channelTitle }
    }
    return { isValid: false, error: 'Channel not found' }
  })
}

export async function getChannelDetails(channelId: string) {
  return withRetry(async (youtube) => {
    const response = await youtube.channels.list({
      part: ['snippet', 'statistics'],
      id: [channelId],
    })
    const channel = response.data.items?.[0]
    if (!channel) return null
    return {
      name: channel.snippet?.title || 'Unknown',
      subscriberCount: parseInt(channel.statistics?.subscriberCount || '0', 10),
      thumbnailUrl: channel.snippet?.thumbnails?.default?.url || '',
    }
  })
}
