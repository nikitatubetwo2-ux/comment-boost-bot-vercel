#!/bin/bash
# Установка Video Factory

echo "🎬 Video Factory - Установка"
echo "=============================="

cd "$(dirname "$0")"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.9+"
    exit 1
fi

echo "✓ Python3 найден: $(python3 --version)"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация
source venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Проверка FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg не найден. Для монтажа видео установите:"
    echo "   brew install ffmpeg"
fi

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Для запуска:"
echo "   ./run.sh"
echo ""
echo "Или:"
echo "   source venv/bin/activate"
echo "   python main.py"
