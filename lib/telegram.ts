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
    displayRu: {
      informative: string
      emotional: string
      questionBased: string
    }
    forCopy: {
      informative: string
      emotional: string
      questionBased: string
    }
    videoLanguage: string
  }
): Promise<void> {
  const videoUrl = `https://youtube.com/watch?v=${video.videoId}`
  
  const langNote = comments.videoLanguage !== 'ru' 
    ? `\n\n🌐 _Язык видео: ${comments.videoLanguage.toUpperCase()}. Комментарии для копирования на языке видео._`
    : ''
  
  const message = `🎬 *Новое видео!*

📺 *${video.channelName}*
${escapeMarkdown(video.title)}

🔗 ${videoUrl}${langNote}

💬 *Комментарии:*

1️⃣ *Информативный:*
${escapeMarkdown(comments.displayRu.informative)}
📋 \`${comments.forCopy.informative}\`

2️⃣ *Эмоциональный:*
${escapeMarkdown(comments.displayRu.emotional)}
📋 \`${comments.forCopy.emotional}\`

3️⃣ *Вопрос:*
${escapeMarkdown(comments.displayRu.questionBased)}
📋 \`${comments.forCopy.questionBased}\`

_Нажми на текст в рамке чтобы скопировать_`

  await sendMessage(chatId, message)
}

function escapeMarkdown(text: string): string {
  return text.replace(/[_*[\]()~`>#+=|{}.!-]/g, '\\$&')
}
