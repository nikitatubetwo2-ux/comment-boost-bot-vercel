"""
Task Queue Manager for distributed generation
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import heapq

from .models import (
    GenerationTask, 
    GenerationRequest, 
    TaskStatus, 
    WorkerInfo,
    QueueStats,
)


class QueueManager:
    """Manages generation tasks and worker distribution"""
    
    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        
        # Task storage
        self._tasks: Dict[str, GenerationTask] = {}
        
        # Priority queue: (priority, created_at, task_id)
        self._pending_queue: List[tuple] = []
        
        # Workers
        self._workers: Dict[str, WorkerInfo] = {}
        
        # Stats
        self._completed_count = 0
        self._failed_count = 0
        self._total_generation_time = 0.0
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def add_task(self, request: GenerationRequest) -> GenerationTask:
        """Add a new generation task to the queue"""
        async with self._lock:
            if len(self._pending_queue) >= self.max_queue_size:
                raise ValueError("Queue is full")
            
            task = GenerationTask(request=request)
            self._tasks[task.id] = task
            
            # Add to priority queue (negative priority for max-heap behavior)
            heapq.heappush(
                self._pending_queue,
                (-request.priority, task.created_at.timestamp(), task.id)
            )
            
            return task
    
    async def get_next_task(self, worker_id: str) -> Optional[GenerationTask]:
        """Get the next task for a worker"""
        async with self._lock:
            while self._pending_queue:
                _, _, task_id = heapq.heappop(self._pending_queue)
                task = self._tasks.get(task_id)
                
                if task and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.PROCESSING
                    task.worker_id = worker_id
                    task.started_at = datetime.utcnow()
                    
                    # Update worker status
                    if worker_id in self._workers:
                        self._workers[worker_id].status = "busy"
                        self._workers[worker_id].current_task_id = task_id
                    
                    return task
            
            return None
    
    async def complete_task(
        self, 
        task_id: str, 
        result_paths: List[str],
        duration: float,
    ):
        """Mark a task as completed"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result_paths = result_paths
            
            self._completed_count += 1
            self._total_generation_time += duration
            
            # Update worker
            if task.worker_id and task.worker_id in self._workers:
                worker = self._workers[task.worker_id]
                worker.status = "idle"
                worker.current_task_id = None
                worker.tasks_completed += 1
                
                # Update average generation time
                if worker.avg_generation_time:
                    worker.avg_generation_time = (
                        worker.avg_generation_time * 0.9 + duration * 0.1
                    )
                else:
                    worker.avg_generation_time = duration
    
    async def fail_task(self, task_id: str, error: str):
        """Mark a task as failed"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = error
            
            self._failed_count += 1
            
            # Update worker
            if task.worker_id and task.worker_id in self._workers:
                worker = self._workers[task.worker_id]
                worker.status = "idle"
                worker.current_task_id = None
    
    async def get_task(self, task_id: str) -> Optional[GenerationTask]:
        """Get task by ID"""
        return self._tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                return True
            return False
    
    async def register_worker(self, worker: WorkerInfo):
        """Register a new worker"""
        async with self._lock:
            self._workers[worker.id] = worker
    
    async def unregister_worker(self, worker_id: str):
        """Unregister a worker"""
        async with self._lock:
            if worker_id in self._workers:
                del self._workers[worker_id]
    
    async def worker_heartbeat(self, worker_id: str):
        """Update worker heartbeat"""
        async with self._lock:
            if worker_id in self._workers:
                self._workers[worker_id].last_heartbeat = datetime.utcnow()
    
    async def get_workers(self) -> List[WorkerInfo]:
        """Get all registered workers"""
        return list(self._workers.values())
    
    async def get_stats(self) -> QueueStats:
        """Get queue statistics"""
        pending = sum(
            1 for t in self._tasks.values() 
            if t.status == TaskStatus.PENDING
        )
        processing = sum(
            1 for t in self._tasks.values() 
            if t.status == TaskStatus.PROCESSING
        )
        active_workers = sum(
            1 for w in self._workers.values()
            if w.status != "offline" and 
            (datetime.utcnow() - w.last_heartbeat) < timedelta(minutes=2)
        )
        
        # Estimate wait time
        estimated_wait = None
        if active_workers > 0 and self._completed_count > 0:
            avg_time = self._total_generation_time / self._completed_count
            estimated_wait = (pending / active_workers) * avg_time
        
        return QueueStats(
            pending_tasks=pending,
            processing_tasks=processing,
            completed_tasks=self._completed_count,
            failed_tasks=self._failed_count,
            active_workers=active_workers,
            estimated_wait_time=estimated_wait,
        )
    
    async def get_recent_tasks(self, limit: int = 50) -> List[GenerationTask]:
        """Get recent tasks"""
        tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )
        return tasks[:limit]
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove old completed/failed tasks"""
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
            to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
                and task.created_at < cutoff
            ]
            for task_id in to_remove:
                del self._tasks[task_id]
            
            return len(to_remove)
