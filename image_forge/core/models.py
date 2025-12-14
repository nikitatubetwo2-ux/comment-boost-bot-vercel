"""
Data models for ImageForge
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationRequest(BaseModel):
    """Request for image generation"""
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str = Field(default="", max_length=1000)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    steps: int = Field(default=28, ge=1, le=100)
    guidance: float = Field(default=3.5, ge=1.0, le=20.0)
    seed: Optional[int] = Field(default=None)
    batch_size: int = Field(default=1, ge=1, le=4)
    priority: int = Field(default=0, ge=0, le=10)  # Higher = more priority
    
    # Metadata
    project_id: Optional[str] = None
    callback_url: Optional[str] = None


class GenerationTask(BaseModel):
    """Task in the queue"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: GenerationRequest
    status: TaskStatus = TaskStatus.PENDING
    worker_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_paths: List[str] = Field(default_factory=list)
    
    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class GenerationResult(BaseModel):
    """Result of image generation"""
    task_id: str
    status: TaskStatus
    images: List[str] = Field(default_factory=list)  # Base64 or URLs
    seed_used: Optional[int] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class WorkerInfo(BaseModel):
    """Information about a worker"""
    id: str
    device: str  # cuda, mps, cpu
    device_name: str  # RTX 3060 Ti, Apple M3, etc.
    vram_gb: Optional[float] = None
    status: str = "idle"  # idle, busy, offline
    current_task_id: Optional[str] = None
    tasks_completed: int = 0
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    avg_generation_time: Optional[float] = None


class QueueStats(BaseModel):
    """Queue statistics"""
    pending_tasks: int = 0
    processing_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    active_workers: int = 0
    estimated_wait_time: Optional[float] = None
