"""
Пакетная обработка — создание нескольких роликов
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class VideoTask:
    """Задача на создание видео"""
    id: str
    title: str
    topic: str
    duration: str
    style: str
    status: str = "pending"
    progress: int = 0
    current_stage: str = ""
    error: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    output_path: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)


class BatchProcessor:
    """Пакетный процессор для создания нескольких видео"""
    
    STAGES = [
        ("script", "Генерация сценария", 15),
        ("images", "Генерация промптов для изображений", 10),
        ("voice", "Озвучка", 30),
        ("render", "Рендер видео", 35),
        ("seo", "SEO оптимизация", 5),
        ("export", "Экспорт", 5)
    ]
    
    def __init__(self, queue_dir: Path, output_dir: Path):
        self.queue_dir = queue_dir
        self.output_dir = output_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks: List[VideoTask] = []
        self.is_running = False
        self.current_task: Optional[VideoTask] = None
        
        # Callbacks
        self.on_progress: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def add_task(self, title: str, topic: str, duration: str = "20-30 минут", style: str = "Документальный") -> VideoTask:
        """Добавление задачи в очередь"""
        task_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
        
        task = VideoTask(
            id=task_id,
            title=title,
            topic=topic,
            duration=duration,
            style=style
        )
        
        self.tasks.append(task)
        self._save_queue()
        
        return task
    
    def add_tasks_from_topics(self, topics: List[Dict], duration: str = "20-30 минут", style: str = "Документальный") -> List[VideoTask]:
        """Добавление нескольких задач из списка тем"""
        added_tasks = []
        
        for topic_data in topics:
            title = topic_data.get('title', topic_data.get('topic', 'Без названия'))
            topic = topic_data.get('description', title)
            
            task = self.add_task(title, topic, duration, style)
            added_tasks.append(task)
        
        return added_tasks
    
    def remove_task(self, task_id: str) -> bool:
        """Удаление задачи"""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                if task.status not in [TaskStatus.RUNNING.value]:
                    self.tasks.pop(i)
                    self._save_queue()
                    return True
        return False
    
    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """Получение задачи по ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_pending_tasks(self) -> List[VideoTask]:
        """Получение задач в ожидании"""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING.value]
    
    def get_completed_tasks(self) -> List[VideoTask]:
        """Получение завершённых задач"""
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED.value]
    
    def start_processing(self, config: Dict[str, Any]):
        """Запуск обработки очереди"""
        self.is_running = True
        self.config = config
        
        while self.is_running:
            pending = self.get_pending_tasks()
            
            if not pending:
                break
            
            task = pending[0]
            self._process_task(task)
        
        self.is_running = False
    
    def stop_processing(self):
        """Остановка обработки"""
        self.is_running = False
    
    def pause_task(self, task_id: str):
        """Пауза задачи"""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.RUNNING.value:
            task.status = TaskStatus.PAUSED.value
            self._save_queue()
    
    def _process_task(self, task: VideoTask):
        """Обработка одной задачи"""
        task.status = TaskStatus.RUNNING.value
        task.started_at = datetime.now().isoformat()
        self.current_task = task
        self._save_queue()
        
        try:
            total_progress = 0
            
            for stage_id, stage_name, stage_weight in self.STAGES:
                if not self.is_running:
                    task.status = TaskStatus.PAUSED.value
                    break
                
                task.current_stage = stage_name
                self._save_queue()
                
                if self.on_progress:
                    self.on_progress(task.id, total_progress, stage_name)
                
                # Выполняем этап
                self._execute_stage(task, stage_id)
                
                total_progress += stage_weight
                task.progress = total_progress
                self._save_queue()
            
            if self.is_running:
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.now().isoformat()
                task.progress = 100
                
                if self.on_task_complete:
                    self.on_task_complete(task)
        
        except Exception as e:
            task.status = TaskStatus.FAILED.value
            task.error = str(e)
            
            if self.on_error:
                self.on_error(task, e)
        
        finally:
            self.current_task = None
            self._save_queue()
    
    def _execute_stage(self, task: VideoTask, stage_id: str):
        """Выполнение этапа"""
        # Здесь будет реальная логика
        # Пока просто имитация
        time.sleep(0.5)  # Имитация работы
    
    def _save_queue(self):
        """Сохранение очереди в файл"""
        queue_file = self.queue_dir / "queue.json"
        
        data = {
            'tasks': [t.to_dict() for t in self.tasks],
            'updated_at': datetime.now().isoformat()
        }
        
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_queue(self):
        """Загрузка очереди из файла"""
        queue_file = self.queue_dir / "queue.json"
        
        if queue_file.exists():
            try:
                with open(queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.tasks = [VideoTask(**t) for t in data.get('tasks', [])]
            except Exception as e:
                print(f"Ошибка загрузки очереди: {e}")
                self.tasks = []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Статистика очереди"""
        return {
            'total': len(self.tasks),
            'pending': len([t for t in self.tasks if t.status == TaskStatus.PENDING.value]),
            'running': len([t for t in self.tasks if t.status == TaskStatus.RUNNING.value]),
            'completed': len([t for t in self.tasks if t.status == TaskStatus.COMPLETED.value]),
            'failed': len([t for t in self.tasks if t.status == TaskStatus.FAILED.value]),
            'paused': len([t for t in self.tasks if t.status == TaskStatus.PAUSED.value]),
        }
    
    def clear_completed(self):
        """Очистка завершённых задач"""
        self.tasks = [t for t in self.tasks if t.status != TaskStatus.COMPLETED.value]
        self._save_queue()
    
    def clear_failed(self):
        """Очистка неудачных задач"""
        self.tasks = [t for t in self.tasks if t.status != TaskStatus.FAILED.value]
        self._save_queue()
    
    def retry_failed(self):
        """Повторная попытка для неудачных задач"""
        for task in self.tasks:
            if task.status == TaskStatus.FAILED.value:
                task.status = TaskStatus.PENDING.value
                task.error = ""
                task.progress = 0
        self._save_queue()
