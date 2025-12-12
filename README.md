# CommentBoost Bot

Telegram бот для мониторинга YouTube каналов конкурентов и генерации комментариев с помощью AI.

## Что делает бот

1. Ты добавляешь каналы конкурентов
2. Бот автоматически мониторит новые видео каждые 15 минут
3. При выходе нового видео — присылает тебе уведомление с 3 вариантами комментариев
4. Комментарии показываются на русском, но копируются на языке видео
5. Ты копируешь комментарий и публикуешь под видео конкурента

## Требования

- Telegram Bot Token (от @BotFather)
- 1-3 YouTube API ключа (рекомендуется 3 для надёжности)
- Groq API ключ (бесплатно на groq.com)
- Upstash Redis (бесплатно)
- Vercel аккаунт (бесплатно)
- Cron-job.org аккаунт (бесплатно)

## Деплой на Vercel

### Шаг 1: GitHub репозиторий
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/comment-boost-bot.git
git push -u origin main
```

### Шаг 2: Upstash Redis (хранилище данных)
1. Зайди на https://upstash.com
2. Создай аккаунт через GitHub
3. Create Database → регион EU West
4. Скопируй `UPSTASH_REDIS_REST_URL` и `UPSTASH_REDIS_REST_TOKEN`

### Шаг 3: Vercel деплой
1. Зайди на https://vercel.com
2. Import Project → выбери репозиторий
3. Добавь Environment Variables:

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather |
| `YOUTUBE_API_KEYS` | Ключи через запятую: `key1,key2,key3` |
| `GROQ_API_KEY` | Ключ от groq.com |
| `KV_REST_API_URL` | URL от Upstash |
| `KV_REST_API_TOKEN` | Token от Upstash |
| `CRON_SECRET` | Любой секрет, например: `mysecret123` |

4. Deploy!

### Шаг 4: Регистрация Webhook
Открой в браузере:
```
https://твой-проект.vercel.app/api/setup
```

### Шаг 5: Проверка статуса и API ключей
Открой в браузере:
```
https://твой-проект.vercel.app/api/status
```
Покажет статус всех API ключей и конфигурации.

### Шаг 6: Настройка Cron (автоматический мониторинг)
1. Зайди на https://cron-job.org
2. Создай аккаунт
3. Create Cronjob:
   - URL: `https://твой-проект.vercel.app/api/cron`
   - Schedule: Every 15 minutes
   - Advanced → Headers: `Authorization: Bearer mysecret123`
4. Save и Enable

## Команды бота

- `/start` — Начало работы
- `/profile Название` — Создать профиль
- `/add @channel` — Добавить канал для мониторинга
- `/channels` — Список отслеживаемых каналов
- `/myid` — Твой Telegram ID
- `/help` — Помощь

## YouTube API лимиты

Каждый API ключ даёт 10,000 единиц в день.
- Поиск видео: ~100 единиц
- Детали видео: ~3 единицы

С 3 ключами можно проверять ~50 каналов каждые 15 минут без проблем.

## Готово!

Бот будет автономно работать и присылать уведомления о новых видео конкурентов.
