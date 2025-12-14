#!/bin/bash
# ImageForge Installation Script

echo "🎨 ImageForge Installation"
echo "=========================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch (detect platform)
echo ""
echo "Installing PyTorch..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use MPS
    pip install torch torchvision torchaudio
elif command -v nvidia-smi &> /dev/null; then
    # NVIDIA GPU
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    # CPU only
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
fi

# Create data directories
mkdir -p data/models data/output data/gallery

echo ""
echo "✅ Installation complete!"
echo ""
echo "To start:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Start master:  python -m image_forge master"
echo "  3. Start worker:  python -m image_forge worker"
echo ""
echo "Web UI will be at: http://localhost:8100"
