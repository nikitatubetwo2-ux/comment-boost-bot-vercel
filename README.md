# CommentBoost Bot (Vercel Serverless)

Telegram бот для мониторинга YouTube каналов и генерации комментариев.

## Деплой на Vercel

### Шаг 1: Создай репозиторий на GitHub
1. Зайди на github.com
2. New repository → `comment-boost-bot-vercel`
3. Запуши этот код

### Шаг 2: Создай Upstash Redis (бесплатное хранилище)
1. Зайди на https://upstash.com
2. Создай аккаунт (через GitHub)
3. Create Database → выбери регион (EU West)
4. Скопируй `UPSTASH_REDIS_REST_URL` и `UPSTASH_REDIS_REST_TOKEN`

### Шаг 3: Деплой на Vercel
1. Зайди на https://vercel.com
2. Import Project → выбери репозиторий
3. Добавь Environment Variables:
   - `TELEGRAM_BOT_TOKEN` = твой токен бота
   - `YOUTUBE_API_KEYS` = ключи через запятую
   - `GROQ_API_KEY` = ключ Groq
   - `KV_REST_API_URL` = URL от Upstash
   - `KV_REST_API_TOKEN` = Token от Upstash
   - `CRON_SECRET` = любой секретный ключ (например: mysecret123)
4. Deploy!

### Шаг 4: Настрой Webhook
После деплоя открой в браузере:
```
https://твой-проект.vercel.app/api/setup
```
Это зарегистрирует webhook в Telegram.

### Шаг 5: Настрой Cron (автопроверка каналов)
1. Зайди на https://cron-job.org
2. Создай аккаунт
3. Create Cronjob:
   - URL: `https://твой-проект.vercel.app/api/cron`
   - Schedule: Every 15 minutes
   - Headers: `Authorization: Bearer mysecret123` (твой CRON_SECRET)
4. Save

## Готово!

Бот будет:
- Отвечать на команды в Telegram
- Каждые 15 минут проверять новые видео
- Отправлять уведомления с готовыми комментариями
