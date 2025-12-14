"""
ImageForge Master Server
Manages queue and serves API
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from . import config
from .api import routes
from .core.queue_manager import QueueManager

# Initialize queue manager
queue_manager = QueueManager(max_queue_size=config.MAX_QUEUE_SIZE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 ImageForge Master starting...")
    routes.queue_manager = queue_manager
    
    # Start cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    print("👋 ImageForge Master shutting down...")


async def periodic_cleanup():
    """Periodically clean up old tasks"""
    while True:
        await asyncio.sleep(3600)  # Every hour
        removed = await queue_manager.cleanup_old_tasks(max_age_hours=24)
        if removed > 0:
            print(f"🧹 Cleaned up {removed} old tasks")


# Create FastAPI app
app = FastAPI(
    title="ImageForge",
    description="Local FLUX image generation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(routes.router, prefix="/api")

# Serve static files (UI)
try:
    app.mount("/", StaticFiles(directory="ui/static", html=True), name="static")
except:
    pass  # UI not built yet


def main():
    """Run the master server"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                      ImageForge Master                       ║
╠══════════════════════════════════════════════════════════════╣
║  API:  http://{config.MASTER_HOST}:{config.MASTER_PORT}/api                          ║
║  Docs: http://{config.MASTER_HOST}:{config.MASTER_PORT}/docs                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host=config.MASTER_HOST,
        port=config.MASTER_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
