// Environment variables
export const config = {
  telegram: {
    botToken: process.env.TELEGRAM_BOT_TOKEN || '',
    webhookSecret: process.env.WEBHOOK_SECRET || 'secret123',
  },
  youtube: {
    apiKeys: (process.env.YOUTUBE_API_KEYS || '')
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0),
  },
  groq: {
    apiKey: process.env.GROQ_API_KEY || '',
    model: 'llama-3.3-70b-versatile',
  },
  // KV storage URL (Vercel KV or Upstash)
  kv: {
    url: process.env.KV_REST_API_URL || '',
    token: process.env.KV_REST_API_TOKEN || '',
  },
}
