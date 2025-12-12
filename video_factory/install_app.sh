#!/bin/bash
# Установка Video Factory как приложения macOS

echo "🎬 Установка Video Factory..."
echo ""

# Путь к текущей папке
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="$APP_DIR/VideoFactory.app"

# Сохраняем путь в конфиг для launcher
echo "$APP_DIR" > "$HOME/.video_factory_path"
echo "📁 Путь сохранён: $APP_DIR"

# Активируем venv
source "$APP_DIR/venv/bin/activate" 2>/dev/null || true

# Создаём иконку
echo "🎨 Создание иконки..."
python "$APP_DIR/create_icon.py"

# Конвертируем в .icns если возможно
if [ -d "AppIcon.iconset" ]; then
    iconutil -c icns AppIcon.iconset 2>/dev/null
    if [ -f "AppIcon.icns" ]; then
        mv AppIcon.icns "$APP_PATH/Contents/Resources/"
        rm -rf AppIcon.iconset
        echo "✅ Иконка .icns создана!"
    fi
fi

# Делаем launcher исполняемым
chmod +x "$APP_PATH/Contents/MacOS/launcher"

# Удаляем старую версию с рабочего стола
rm -rf ~/Desktop/VideoFactory.app 2>/dev/null

# Копируем на рабочий стол
cp -r "$APP_PATH" ~/Desktop/

echo ""
echo "✅ Video Factory установлен на рабочий стол!"
echo ""
echo "📌 Двойной клик на 'Video Factory' чтобы запустить"
echo ""

# Если первый запуск показывает предупреждение:
echo "⚠️  Если macOS блокирует запуск:"
echo "   1. Правый клик на иконку"
echo "   2. Выбери 'Открыть'"
echo "   3. Нажми 'Открыть' в диалоге"
