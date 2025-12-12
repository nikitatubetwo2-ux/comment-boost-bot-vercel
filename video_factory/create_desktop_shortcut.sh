#!/bin/bash
# Создание ярлыка Video Factory на рабочем столе

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP="$HOME/Desktop"
APP_NAME="Video Factory"

# Создаём .app на рабочем столе
mkdir -p "$DESKTOP/$APP_NAME.app/Contents/MacOS"
mkdir -p "$DESKTOP/$APP_NAME.app/Contents/Resources"

# Исполняемый скрипт с абсолютным путём
cat > "$DESKTOP/$APP_NAME.app/Contents/MacOS/run" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"

# Активируем виртуальное окружение
if [ ! -d "venv" ]; then
    /usr/bin/python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Запускаем
python main.py
EOF

chmod +x "$DESKTOP/$APP_NAME.app/Contents/MacOS/run"

# Info.plist
cat > "$DESKTOP/$APP_NAME.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>run</string>
    <key>CFBundleIdentifier</key>
    <string>com.videofactory.app</string>
    <key>CFBundleName</key>
    <string>Video Factory</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

echo "✅ Ярлык создан на рабочем столе: $DESKTOP/$APP_NAME.app"
echo "🎬 Дважды кликните на него для запуска!"
