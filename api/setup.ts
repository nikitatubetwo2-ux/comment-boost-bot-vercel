import type { VercelRequest, VercelResponse } from '@vercel/node'
import { config } from '../lib/config'

// One-time setup endpoint to register webhook with Telegram
export default async function handler(req: VercelRequest, res: VercelResponse) {
  const host = req.headers.host
  const webhookUrl = `https://${host}/api/webhook`
  
  try {
    const response = await fetch(
      `https://api.telegram.org/bot${config.telegram.botToken}/setWebhook`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: webhookUrl,
          allowed_updates: ['message', 'callback_query'],
        }),
      }
    )
    
    const result = await response.json()
    
    res.status(200).json({
      ok: true,
      webhookUrl,
      telegramResponse: result,
    })
  } catch (error) {
    res.status(500).json({ error: String(error) })
  }
}
