import { Telegraf, Context } from 'telegraf'
import { config } from './config'

let bot: Telegraf | null = null

export function getBot(): Telegraf {
  if (!bot) {
    bot = new Telegraf(config.telegram.botToken)
  }
  return bot
}

export async function sendMessage(chatId: number, text: string, options?: object): Promise<void> {
  const bot = getBot()
  await bot.telegram.sendMessage(chatId, text, {
    parse_mode: 'Markdown',
    ...options,
  })
}

export async function sendVideoNotification(
  chatId: number,
  video: {
    title: string
    channelName: string
    thumbnailUrl: string
    videoId: string
  },
  comments: {
    informative: string
    emotional: string
    questionBased: string
  }
): Promise<void> {
  const videoUrl = `https://youtube.com/watch?v=${video.videoId}`
  
  const message = `🎬 *Новое видео!*

📺 *${video.channelName}*
${video.title}

🔗 ${videoUrl}

💬 *Комментарии для копирования:*

1️⃣ *Информативный:*
\`${comments.informative}\`

2️⃣ *Эмоциональный:*
\`${comments.emotional}\`

3️⃣ *Вопрос:*
\`${comments.questionBased}\`

_Нажми на комментарий чтобы скопировать_`

  await sendMessage(chatId, message)
}
