"""
API Routes for ImageForge
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
from pathlib import Path
import asyncio

from ..core.models import (
    GenerationRequest,
    GenerationResult,
    GenerationTask,
    TaskStatus,
    WorkerInfo,
    QueueStats,
)
from ..core.queue_manager import QueueManager
from .. import config

router = APIRouter()

# Global queue manager (initialized in main)
queue_manager: Optional[QueueManager] = None


def get_queue() -> QueueManager:
    if queue_manager is None:
        raise HTTPException(status_code=500, detail="Queue not initialized")
    return queue_manager


# ============== Generation Endpoints ==============

@router.post("/generate", response_model=GenerationTask)
async def create_generation(request: GenerationRequest):
    """Submit a new image generation request"""
    queue = get_queue()
    try:
        task = await queue.add_task(request)
        return task
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/task/{task_id}", response_model=GenerationTask)
async def get_task(task_id: str):
    """Get task status and result"""
    queue = get_queue()
    task = await queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a pending task"""
    queue = get_queue()
    success = await queue.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Task cannot be cancelled (not pending)"
        )
    return {"status": "cancelled"}


@router.post("/generate/sync", response_model=GenerationResult)
async def generate_sync(request: GenerationRequest):
    """
    Synchronous generation - waits for result
    Use for single images when you need immediate result
    """
    queue = get_queue()
    task = await queue.add_task(request)
    
    # Poll for completion
    max_wait = 300  # 5 minutes
    poll_interval = 1
    waited = 0
    
    while waited < max_wait:
        await asyncio.sleep(poll_interval)
        waited += poll_interval
        
        task = await queue.get_task(task.id)
        if task.status == TaskStatus.COMPLETED:
            return GenerationResult(
                task_id=task.id,
                status=task.status,
                images=task.result_paths,
                duration_seconds=task.duration,
            )
        elif task.status == TaskStatus.FAILED:
            return GenerationResult(
                task_id=task.id,
                status=task.status,
                error=task.error,
            )
    
    raise HTTPException(status_code=408, detail="Generation timeout")


@router.get("/image/{task_id}/{index}")
async def get_image(task_id: str, index: int = 0):
    """Get generated image file"""
    queue = get_queue()
    task = await queue.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed")
    
    if index >= len(task.result_paths):
        raise HTTPException(status_code=404, detail="Image index out of range")
    
    image_path = Path(task.result_paths[index])
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    
    return FileResponse(image_path, media_type="image/png")


# ============== Batch Endpoints ==============

@router.post("/batch/generate", response_model=List[GenerationTask])
async def create_batch(requests: List[GenerationRequest]):
    """Submit multiple generation requests"""
    queue = get_queue()
    tasks = []
    
    for request in requests:
        try:
            task = await queue.add_task(request)
            tasks.append(task)
        except ValueError:
            break  # Queue full
    
    return tasks


# ============== Queue & Stats Endpoints ==============

@router.get("/queue/stats", response_model=QueueStats)
async def get_queue_stats():
    """Get queue statistics"""
    queue = get_queue()
    return await queue.get_stats()


@router.get("/queue/tasks", response_model=List[GenerationTask])
async def get_recent_tasks(limit: int = 50):
    """Get recent tasks"""
    queue = get_queue()
    return await queue.get_recent_tasks(limit)


# ============== Worker Endpoints ==============

@router.get("/workers", response_model=List[WorkerInfo])
async def get_workers():
    """Get all registered workers"""
    queue = get_queue()
    return await queue.get_workers()


@router.post("/worker/register")
async def register_worker(worker: WorkerInfo):
    """Register a new worker"""
    queue = get_queue()
    await queue.register_worker(worker)
    return {"status": "registered"}


@router.post("/worker/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str):
    """Worker heartbeat"""
    queue = get_queue()
    await queue.worker_heartbeat(worker_id)
    return {"status": "ok"}


@router.get("/worker/{worker_id}/task", response_model=Optional[GenerationTask])
async def get_worker_task(worker_id: str):
    """Get next task for worker"""
    queue = get_queue()
    task = await queue.get_next_task(worker_id)
    return task


@router.post("/worker/{worker_id}/complete")
async def complete_worker_task(
    worker_id: str,
    task_id: str,
    result_paths: List[str],
    duration: float,
):
    """Mark task as completed by worker"""
    queue = get_queue()
    await queue.complete_task(task_id, result_paths, duration)
    return {"status": "completed"}


@router.post("/worker/{worker_id}/fail")
async def fail_worker_task(worker_id: str, task_id: str, error: str):
    """Mark task as failed by worker"""
    queue = get_queue()
    await queue.fail_task(task_id, error)
    return {"status": "failed"}


# ============== Health ==============

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    queue = get_queue()
    stats = await queue.get_stats()
    return {
        "status": "healthy",
        "workers": stats.active_workers,
        "pending_tasks": stats.pending_tasks,
    }
