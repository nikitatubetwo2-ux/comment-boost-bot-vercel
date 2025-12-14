#!/bin/bash
# Start ImageForge Master Server

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting ImageForge Master..."
python -m image_forge master
