#!/bin/bash
# Start ImageForge Worker

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Default values
MASTER_URL="${MASTER_URL:-http://localhost:8100}"
WORKER_ID="${WORKER_ID:-worker-$(hostname)}"
DEVICE="${DEVICE:-auto}"

echo "🔧 Starting ImageForge Worker..."
echo "   Master: $MASTER_URL"
echo "   Worker ID: $WORKER_ID"
echo "   Device: $DEVICE"

python -m image_forge worker \
    --master "$MASTER_URL" \
    --id "$WORKER_ID" \
    --device "$DEVICE"
