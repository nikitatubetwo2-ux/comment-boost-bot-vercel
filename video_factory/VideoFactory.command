#!/bin/bash
# Video Factory Launcher

# Путь к приложению
APP_DIR="/Users/nikitamoskalev/Desktop/pricing/comment-boost-bot-vercel/comment-boost-bot-vercel/video_factory"

cd "$APP_DIR" || exit 1

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем
python main.py
