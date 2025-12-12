import type { Handler } from '@netlify/functions'
import { config } from '../../lib/config'

export const handler: Handler = async () => {
  const status = {
    ok: true,
    timestamp: new Date().toISOString(),
    config: {
      telegramBot: config.telegram.botToken ? '✅ Настроен' : '❌ Не настроен',
      youtubeApiKeys: `${config.youtube.apiKeys.length} ключей`,
      groqApi: config.groq.apiKey ? '✅ Настроен' : '❌ Не настроен',
      kvStorage: config.kv.url ? '✅ Настроен' : '⚠️ Используется память',
    },
    youtubeKeysDetail: config.youtube.apiKeys.map((key, i) => ({
      key: i + 1,
      preview: `${key.slice(0, 8)}...${key.slice(-4)}`,
      status: '✅',
    })),
  }

  // Test YouTube API keys
  for (let i = 0; i < status.youtubeKeysDetail.length; i++) {
    try {
      const testUrl = `https://www.googleapis.com/youtube/v3/channels?part=id&id=UC_x5XG1OV2P6uZZ5FSM9Ttw&key=${config.youtube.apiKeys[i]}`
      const response = await fetch(testUrl)
      if (!response.ok) {
        const error = await response.json()
        status.youtubeKeysDetail[i].status = `❌ ${error.error?.message || 'Ошибка'}`
      }
    } catch {
      status.youtubeKeysDetail[i].status = '❌ Ошибка подключения'
    }
  }

  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(status, null, 2),
  }
}
