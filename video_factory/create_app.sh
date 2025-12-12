#!/bin/bash
# Создание .app для macOS

APP_NAME="Video Factory"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Создаём структуру .app
mkdir -p "$SCRIPT_DIR/$APP_NAME.app/Contents/MacOS"
mkdir -p "$SCRIPT_DIR/$APP_NAME.app/Contents/Resources"

# Создаём исполняемый скрипт
cat > "$SCRIPT_DIR/$APP_NAME.app/Contents/MacOS/VideoFactory" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../../../"

if [ ! -d "venv" ]; then
    osascript -e 'display notification "Первый запуск - установка..." with title "Video Factory"'
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

python main.py
EOF

chmod +x "$SCRIPT_DIR/$APP_NAME.app/Contents/MacOS/VideoFactory"

# Создаём Info.plist
cat > "$SCRIPT_DIR/$APP_NAME.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>VideoFactory</string>
    <key>CFBundleIdentifier</key>
    <string>com.videofactory.app</string>
    <key>CFBundleName</key>
    <string>Video Factory</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>
EOF

echo "✅ Приложение создано: $SCRIPT_DIR/$APP_NAME.app"
echo "📌 Перетащите его в папку Программы или на Dock"
