import type { Handler } from '@netlify/functions'
import { config } from '../../lib/config'

export const handler: Handler = async (event) => {
  const host = event.headers.host
  const webhookUrl = `https://${host}/.netlify/functions/webhook`
  
  try {
    // Delete existing webhook
    await fetch(`https://api.telegram.org/bot${config.telegram.botToken}/deleteWebhook`)
    
    // Set new webhook
    const response = await fetch(
      `https://api.telegram.org/bot${config.telegram.botToken}/setWebhook?url=${encodeURIComponent(webhookUrl)}`
    )
    const result = await response.json()
    
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/html' },
      body: `
        <html>
          <body style="font-family: sans-serif; padding: 40px;">
            <h1>🤖 CommentBoost Bot Setup</h1>
            <p><strong>Webhook URL:</strong> ${webhookUrl}</p>
            <p><strong>Result:</strong> ${JSON.stringify(result)}</p>
            ${result.ok ? '<p style="color: green;">✅ Webhook установлен!</p>' : '<p style="color: red;">❌ Ошибка</p>'}
            <p>Теперь открой бота в Telegram и напиши /start</p>
          </body>
        </html>
      `
    }
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: String(error) })
    }
  }
}
