import type { VercelRequest, VercelResponse } from '@vercel/node'
import { Telegraf } from 'telegraf'
import { config } from '../lib/config'
import * as storage from '../lib/storage'
import { validateChannel, getChannelDetails } from '../lib/youtube'

const bot = new Telegraf(config.telegram.botToken)

// Commands
bot.command('start', async (ctx) => {
  const user = await storage.getOrCreateUser(ctx.from!.id)
  const profiles = await storage.getProfiles(user.id)
  
  await ctx.replyWithMarkdown(`🎯 *CommentBoost Bot*

Я помогу тебе быстро комментировать видео конкурентов!

${profiles.length > 0 ? '✅ У тебя есть профили' : '📝 Создай профиль чтобы начать'}

*Команды:*
/profile - Создать профиль
/add - Добавить канал для мониторинга
/channels - Список каналов
/help - Помощь`)
})

bot.command('help', async (ctx) => {
  await ctx.replyWithMarkdown(`📖 *Как пользоваться:*

1️⃣ Создай профиль: /profile Название
2️⃣ Добавь каналы конкурентов: /add @channelname
3️⃣ Жди уведомления о новых видео
4️⃣ Копируй готовые комментарии

*Команды:*
/profile [имя] - Создать профиль
/add [канал] - Добавить канал
/channels - Список каналов
/myid - Твой Telegram ID`)
})

bot.command('myid', async (ctx) => {
  await ctx.reply(`🆔 Твой ID: \`${ctx.from!.id}\``, { parse_mode: 'Markdown' })
})

bot.command('profile', async (ctx) => {
  const name = ctx.message.text.replace('/profile', '').trim()
  if (!name) {
    await ctx.reply('Укажи имя профиля: /profile МойПрофиль')
    return
  }
  
  const user = await storage.getOrCreateUser(ctx.from!.id)
  const profile = await storage.createProfile(user.id, name)
  await storage.setActiveProfile(user.id, profile.id)
  
  await ctx.replyWithMarkdown(`✅ Профиль *${name}* создан!\n\nТеперь добавь каналы: /add @channelname`)
})

bot.command('add', async (ctx) => {
  const input = ctx.message.text.replace('/add', '').trim()
  if (!input) {
    await ctx.reply('Укажи канал: /add @channelname или ссылку')
    return
  }
  
  const user = await storage.getOrCreateUser(ctx.from!.id)
  if (!user.activeProfileId) {
    await ctx.reply('Сначала создай профиль: /profile МойПрофиль')
    return
  }
  
  await ctx.reply('🔍 Проверяю канал...')
  
  const validation = await validateChannel(input)
  if (!validation.isValid || !validation.channelId) {
    await ctx.reply('❌ Канал не найден. Проверь ссылку или имя.')
    return
  }
  
  const details = await getChannelDetails(validation.channelId)
  if (!details) {
    await ctx.reply('❌ Не удалось получить информацию о канале')
    return
  }
  
  await storage.addChannel(user.activeProfileId, {
    youtubeId: validation.channelId,
    name: details.name,
    subscriberCount: details.subscriberCount,
  })
  
  await ctx.replyWithMarkdown(`✅ Канал *${details.name}* добавлен!\n\n📊 ${details.subscriberCount.toLocaleString()} подписчиков`)
})

bot.command('channels', async (ctx) => {
  const user = await storage.getOrCreateUser(ctx.from!.id)
  if (!user.activeProfileId) {
    await ctx.reply('Сначала создай профиль: /profile МойПрофиль')
    return
  }
  
  const channels = await storage.getChannels(user.activeProfileId)
  if (channels.length === 0) {
    await ctx.reply('У тебя пока нет каналов. Добавь: /add @channelname')
    return
  }
  
  const list = channels.map((c, i) => `${i + 1}. ${c.name}`).join('\n')
  await ctx.replyWithMarkdown(`📺 *Твои каналы:*\n\n${list}`)
})

// Handle text messages
bot.on('text', async (ctx) => {
  const text = ctx.message.text
  
  // If looks like YouTube URL, try to add as channel
  if (text.includes('youtube.com') || text.startsWith('@')) {
    const user = await storage.getOrCreateUser(ctx.from!.id)
    if (!user.activeProfileId) {
      await ctx.reply('Сначала создай профиль: /profile МойПрофиль')
      return
    }
    
    await ctx.reply('🔍 Проверяю канал...')
    const validation = await validateChannel(text)
    
    if (validation.isValid && validation.channelId) {
      const details = await getChannelDetails(validation.channelId)
      if (details) {
        await storage.addChannel(user.activeProfileId, {
          youtubeId: validation.channelId,
          name: details.name,
          subscriberCount: details.subscriberCount,
        })
        await ctx.replyWithMarkdown(`✅ Канал *${details.name}* добавлен!`)
        return
      }
    }
    
    await ctx.reply('❌ Канал не найден')
  }
})

// Webhook handler
export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(200).json({ ok: true, message: 'Bot webhook endpoint' })
  }
  
  try {
    await bot.handleUpdate(req.body)
    res.status(200).json({ ok: true })
  } catch (error) {
    console.error('Webhook error:', error)
    res.status(200).json({ ok: true }) // Always return 200 to Telegram
  }
}
