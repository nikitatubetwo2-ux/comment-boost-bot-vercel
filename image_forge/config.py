"""
ImageForge Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
OUTPUT_DIR = DATA_DIR / "output"
GALLERY_DIR = DATA_DIR / "gallery"

# Create directories
for dir_path in [DATA_DIR, MODELS_DIR, OUTPUT_DIR, GALLERY_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Server
MASTER_HOST = os.getenv("MASTER_HOST", "0.0.0.0")
MASTER_PORT = int(os.getenv("MASTER_PORT", "8100"))
MASTER_URL = os.getenv("MASTER_URL", f"http://localhost:{MASTER_PORT}")

# Worker
WORKER_ID = os.getenv("WORKER_ID", "worker-1")
WORKER_DEVICE = os.getenv("WORKER_DEVICE", "auto")  # auto, cuda, mps, cpu

# FLUX Model Settings
FLUX_MODEL = os.getenv("FLUX_MODEL", "black-forest-labs/FLUX.1-dev")
FLUX_DTYPE = os.getenv("FLUX_DTYPE", "float16")  # float16, bfloat16, float32

# Generation Defaults
DEFAULT_WIDTH = int(os.getenv("DEFAULT_WIDTH", "1024"))
DEFAULT_HEIGHT = int(os.getenv("DEFAULT_HEIGHT", "1024"))
DEFAULT_STEPS = int(os.getenv("DEFAULT_STEPS", "28"))
DEFAULT_GUIDANCE = float(os.getenv("DEFAULT_GUIDANCE", "3.5"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "1000"))

# Memory Optimization (for 8GB VRAM)
ENABLE_CPU_OFFLOAD = os.getenv("ENABLE_CPU_OFFLOAD", "true").lower() == "true"
ENABLE_ATTENTION_SLICING = os.getenv("ENABLE_ATTENTION_SLICING", "true").lower() == "true"
ENABLE_VAE_TILING = os.getenv("ENABLE_VAE_TILING", "true").lower() == "true"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR}/imageforge.db")

# Redis (optional, for distributed queue)
REDIS_URL = os.getenv("REDIS_URL", None)

# API Keys (for future cloud fallback)
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY", "")
FAL_API_KEY = os.getenv("FAL_API_KEY", "")
