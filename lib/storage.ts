// Simple KV storage using Upstash Redis (free tier)
import { config } from './config'

interface StorageData {
  users: Record<string, UserData>
  profiles: Record<string, ProfileData>
  channels: Record<string, ChannelData>
  processedVideos: string[]
}

interface UserData {
  id: number
  activeProfileId: string | null
  createdAt: string
}

interface ProfileData {
  id: string
  userId: number
  name: string
  niche: string
  language: 'ru' | 'en'
  notificationsEnabled: boolean
}

interface ChannelData {
  id: string
  profileId: string
  youtubeId: string
  name: string
  subscriberCount: number
}

// In-memory fallback for development
let memoryStorage: StorageData = {
  users: {},
  profiles: {},
  channels: {},
  processedVideos: [],
}

async function kvFetch(method: string, args: unknown[] = []): Promise<unknown> {
  if (!config.kv.url || !config.kv.token) {
    return null // Use memory storage
  }

  const response = await fetch(`${config.kv.url}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.kv.token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify([method, ...args]),
  })

  const data = await response.json() as { result: unknown }
  return data.result
}

export async function getData(): Promise<StorageData> {
  if (!config.kv.url) {
    return memoryStorage
  }

  const data = await kvFetch('get', ['bot_data'])
  if (data) {
    return JSON.parse(data as string)
  }
  return memoryStorage
}

export async function saveData(data: StorageData): Promise<void> {
  if (!config.kv.url) {
    memoryStorage = data
    return
  }

  await kvFetch('set', ['bot_data', JSON.stringify(data)])
}

// Helper functions
export async function getUser(userId: number): Promise<UserData | null> {
  const data = await getData()
  return data.users[userId.toString()] || null
}

export async function createUser(userId: number): Promise<UserData> {
  const data = await getData()
  const user: UserData = {
    id: userId,
    activeProfileId: null,
    createdAt: new Date().toISOString(),
  }
  data.users[userId.toString()] = user
  await saveData(data)
  return user
}

export async function getOrCreateUser(userId: number): Promise<UserData> {
  const existing = await getUser(userId)
  if (existing) return existing
  return createUser(userId)
}

export async function setActiveProfile(userId: number, profileId: string | null): Promise<void> {
  const data = await getData()
  if (data.users[userId.toString()]) {
    data.users[userId.toString()].activeProfileId = profileId
    await saveData(data)
  }
}

export async function getProfiles(userId: number): Promise<ProfileData[]> {
  const data = await getData()
  return Object.values(data.profiles).filter(p => p.userId === userId)
}

export async function createProfile(userId: number, name: string): Promise<ProfileData> {
  const data = await getData()
  const id = `profile_${Date.now()}`
  const profile: ProfileData = {
    id,
    userId,
    name,
    niche: '',
    language: 'ru',
    notificationsEnabled: true,
  }
  data.profiles[id] = profile
  await saveData(data)
  return profile
}

export async function getChannels(profileId: string): Promise<ChannelData[]> {
  const data = await getData()
  return Object.values(data.channels).filter(c => c.profileId === profileId)
}

export async function addChannel(profileId: string, channel: Omit<ChannelData, 'id' | 'profileId'>): Promise<ChannelData> {
  const data = await getData()
  const id = `channel_${Date.now()}`
  const newChannel: ChannelData = { id, profileId, ...channel }
  data.channels[id] = newChannel
  await saveData(data)
  return newChannel
}

export async function isVideoProcessed(videoId: string): Promise<boolean> {
  const data = await getData()
  return data.processedVideos.includes(videoId)
}

export async function markVideoProcessed(videoId: string): Promise<void> {
  const data = await getData()
  if (!data.processedVideos.includes(videoId)) {
    data.processedVideos.push(videoId)
    // Keep only last 1000 videos
    if (data.processedVideos.length > 1000) {
      data.processedVideos = data.processedVideos.slice(-1000)
    }
    await saveData(data)
  }
}

export async function getAllChannels(): Promise<ChannelData[]> {
  const data = await getData()
  return Object.values(data.channels)
}

export async function getProfileById(profileId: string): Promise<ProfileData | null> {
  const data = await getData()
  return data.profiles[profileId] || null
}
