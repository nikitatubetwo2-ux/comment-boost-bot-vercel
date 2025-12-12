"""
Умный пайплайн — автоматическая генерация видео с AI подбором параметров
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading


class ProjectStatus(Enum):
    """Статусы проекта"""
    QUEUED = "queued"           # В очереди
    ANALYZING = "analyzing"      # Анализ конкурента
    SCRIPTING = "scripting"      # Генерация сценария
    GENERATING_IMAGES = "generating_images"  # Генерация картинок
    GENERATING_VOICE = "generating_voice"    # Озвучка
    ASSEMBLING = "assembling"    # Сборка превью
    READY_FOR_REVIEW = "ready"   # Готов к проверке
    RENDERING = "rendering"      # Финальный рендер
    COMPLETED = "completed"      # Завершён
    ERROR = "error"              # Ошибка
    PAUSED = "paused"            # На паузе


@dataclass
class SmartProject:
    """Умный проект с автоподбором параметров"""
    
    # Идентификация
    id: str
    name: str
    created_at: str = ""
    
    # Входные данные
    topic: str = ""                    # Тема видео
    competitor_channel: str = ""        # Канал конкурента для копирования стиля
    duration: str = "20-30 минут"      # Длительность
    language: str = "Русский"          # Язык
    
    # ПРОФИЛЬ КАНАЛА (для запоминания стиля)
    channel_style_id: str = ""         # ID профиля канала
    sub_niche: str = ""                # Подниша канала
    
    # AI-подобранные параметры
    ai_style: str = ""                 # Стиль повествования (от AI)
    ai_image_style: str = ""           # Стиль изображений (от AI)
    ai_transitions: List[str] = field(default_factory=list)  # Переходы
    ai_effects: Dict[str, Any] = field(default_factory=dict)  # Эффекты
    ai_music_mood: str = ""            # Настроение музыки
    ai_voice: str = ""                 # Рекомендованный голос
    ai_voice_id: str = ""              # ID голоса
    
    # Сгенерированный контент
    script: str = ""
    script_segments: List[Dict] = field(default_factory=list)  # Сегменты с таймкодами
    image_prompts: List[Dict] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    thumbnails: List[str] = field(default_factory=list)  # 3 варианта превью для A/B теста
    thumbnail_prompts: List[Dict] = field(default_factory=list)  # Промпты для превью [{type, prompt, why_viral, path}]
    audio_path: str = ""
    preview_video: str = ""            # Превью для проверки
    final_video: str = ""              # Финальное видео
    
    # Синхронизация картинка-озвучка
    sync_data: List[Dict] = field(default_factory=list)  # [{image, text, start, end}, ...]
    
    # SEO
    seo_title: str = ""
    seo_description: str = ""
    seo_tags: List[str] = field(default_factory=list)
    seo_hashtags: List[str] = field(default_factory=list)
    seo_alt_titles: List[str] = field(default_factory=list)  # A/B варианты заголовков
    seo_first_comment: str = ""  # Текст для закреплённого комментария
    
    # Статус
    status: str = "queued"
    progress: int = 0
    current_step: str = ""
    error_message: str = ""
    
    # Правки пользователя
    user_edits: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SmartProject':
        # Обработка новых полей
        for key in ['script_segments', 'sync_data', 'thumbnails', 'thumbnail_prompts']:
            if key not in data:
                data[key] = []
        if 'channel_style_id' not in data:
            data['channel_style_id'] = ""
        if 'ai_voice_id' not in data:
            data['ai_voice_id'] = ""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SmartPipeline:
    """
    Умный пайплайн для автоматической генерации видео
    
    Возможности:
    - Анализ конкурента и копирование стиля
    - AI подбор эффектов, переходов, музыки
    - Пакетная обработка (очередь проектов)
    - Генерация превью для проверки
    - Применение правок пользователя
    """
    
    def __init__(self, output_dir: Path = None, on_progress: Callable = None):
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.on_progress = on_progress
        self.projects: Dict[str, SmartProject] = {}
        self.queue: List[str] = []  # ID проектов в очереди
        self.is_running = False
        self.current_project_id: Optional[str] = None
        self._worker_thread: Optional[threading.Thread] = None
        
        # Загружаем сохранённые проекты
        self._load_projects()
    
    def _log(self, message: str):
        """Логирование"""
        print(f"[Pipeline] {message}")
        if self.on_progress:
            self.on_progress(message)
    
    def _save_projects(self):
        """Сохранение проектов"""
        data = {pid: p.to_dict() for pid, p in self.projects.items()}
        save_path = self.output_dir / "projects.json"
        save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def _load_projects(self):
        """Загрузка проектов"""
        save_path = self.output_dir / "projects.json"
        if save_path.exists():
            try:
                data = json.loads(save_path.read_text())
                for pid, pdata in data.items():
                    self.projects[pid] = SmartProject.from_dict(pdata)
            except:
                pass
    
    def create_project(self, name: str, topic: str, competitor_channel: str = "",
                       duration: str = "20-30 минут", language: str = "Русский") -> SmartProject:
        """Создание нового проекта"""
        project_id = f"proj_{int(time.time())}_{len(self.projects)}"
        
        project = SmartProject(
            id=project_id,
            name=name,
            created_at=datetime.now().isoformat(),
            topic=topic,
            competitor_channel=competitor_channel,
            duration=duration,
            language=language
        )
        
        self.projects[project_id] = project
        self._save_projects()
        
        return project
    
    def add_to_queue(self, project_id: str):
        """Добавление проекта в очередь"""
        if project_id in self.projects and project_id not in self.queue:
            self.queue.append(project_id)
            self.projects[project_id].status = ProjectStatus.QUEUED.value
            self._save_projects()
    
    def remove_from_queue(self, project_id: str):
        """Удаление из очереди"""
        if project_id in self.queue:
            self.queue.remove(project_id)
    
    def start_queue(self):
        """Запуск обработки очереди"""
        if self.is_running:
            return
        
        self.is_running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
    
    def stop_queue(self):
        """Остановка очереди"""
        self.is_running = False
    
    def _process_queue(self):
        """Обработка очереди проектов с предзагрузкой"""
        successful = 0
        failed = 0
        total = len(self.queue)
        
        # Кэш для предзагруженных данных следующего проекта
        preloaded_data = {}
        
        while self.is_running and self.queue:
            project_id = self.queue[0]
            self.current_project_id = project_id
            
            # Предзагрузка следующего проекта (если есть)
            next_project_id = self.queue[1] if len(self.queue) > 1 else None
            if next_project_id and next_project_id not in preloaded_data:
                self._preload_project(next_project_id, preloaded_data)
            
            try:
                # Используем предзагруженные данные если есть
                self._process_project(project_id, preloaded_data.get(project_id))
                
                # Очищаем использованные данные
                if project_id in preloaded_data:
                    del preloaded_data[project_id]
                
                self.queue.pop(0)
                successful += 1
                
                # Telegram уведомление о готовности проекта
                self._notify_project_ready(project_id)
                
            except Exception as e:
                self._log(f"Ошибка проекта {project_id}: {e}")
                self.projects[project_id].status = ProjectStatus.ERROR.value
                self.projects[project_id].error_message = str(e)
                self.queue.pop(0)
                failed += 1
                
                # Telegram уведомление об ошибке
                self._notify_project_error(project_id, str(e))
            
            self._save_projects()
        
        # Уведомление о завершении очереди
        if total > 0:
            self._notify_queue_complete(total, successful, failed)
        
        self.is_running = False
        self.current_project_id = None
    
    def _notify_project_ready(self, project_id: str):
        """Telegram уведомление о готовности проекта"""
        try:
            from .telegram_notifier import get_notifier
            project = self.projects.get(project_id)
            if not project:
                return
            
            notifier = get_notifier()
            if not notifier.enabled:
                return
            
            # Ищем первую картинку для превью
            preview_path = None
            if project.images:
                from pathlib import Path
                for img in project.images:
                    p = Path(img)
                    if p.exists():
                        preview_path = p
                        break
            
            notifier.notify_project_ready(
                project_name=project.name,
                preview_path=preview_path,
                seo_title=project.seo_title,
                images_count=len(project.images)
            )
        except Exception as e:
            self._log(f"Ошибка Telegram уведомления: {e}")
    
    def _notify_project_error(self, project_id: str, error: str):
        """Telegram уведомление об ошибке"""
        try:
            from .telegram_notifier import get_notifier
            project = self.projects.get(project_id)
            if not project:
                return
            
            notifier = get_notifier()
            if notifier.enabled:
                notifier.notify_project_error(project.name, error)
        except Exception as e:
            self._log(f"Ошибка Telegram уведомления: {e}")
    
    def _notify_queue_complete(self, total: int, successful: int, failed: int):
        """Telegram уведомление о завершении очереди"""
        try:
            from .telegram_notifier import get_notifier
            notifier = get_notifier()
            if notifier.enabled:
                notifier.notify_queue_complete(total, successful, failed)
        except Exception as e:
            self._log(f"Ошибка Telegram уведомления: {e}")
    
    def _preload_project(self, project_id: str, cache: dict):
        """
        Предзагрузка данных следующего проекта
        
        Пока текущий проект рендерится, загружаем данные для следующего:
        - Анализ конкурента
        - Генерация промптов для изображений
        
        Это экономит 30-60 секунд на каждом проекте!
        """
        try:
            project = self.projects.get(project_id)
            if not project:
                return
            
            self._log(f"[Preload] Предзагрузка данных для: {project.name}")
            
            from .youtube_analyzer import YouTubeAnalyzer
            from .groq_client import GroqClient
            from config import config
            
            preload_data = {}
            
            # Предзагрузка данных конкурента
            if project.competitor_channel:
                try:
                    analyzer = YouTubeAnalyzer(config.api.youtube_keys)
                    channel_info = analyzer.get_channel_info(project.competitor_channel)
                    
                    if channel_info:
                        videos = analyzer.get_channel_videos(channel_info.id, max_results=15)
                        preload_data['channel_info'] = channel_info
                        preload_data['videos'] = videos
                        preload_data['titles'] = [v.title for v in videos]
                        preload_data['descriptions'] = [v.description for v in videos if v.description]
                        self._log(f"[Preload] ✅ Данные конкурента загружены")
                except Exception as e:
                    self._log(f"[Preload] Ошибка загрузки конкурента: {e}")
            
            cache[project_id] = preload_data
            
        except Exception as e:
            self._log(f"[Preload] Ошибка: {e}")
    
    def _process_project(self, project_id: str, preloaded_data: dict = None):
        """Полная обработка одного проекта"""
        project = self.projects[project_id]
        project_dir = self.output_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем предзагруженные данные
        if preloaded_data:
            project.user_edits['preloaded'] = preloaded_data
            self._log(f"[{project.name}] Используем предзагруженные данные")
        
        # Шаги 1-2: последовательно (нужен сценарий для остального)
        sequential_steps = [
            ("Анализ конкурента", lambda: self._step_analyze_competitor(project) if project.competitor_channel else self._step_set_defaults(project)),
            ("Генерация сценария", lambda: self._step_generate_script(project)),
        ]
        
        for step_name, step_func in sequential_steps:
            if not self.is_running:
                self._log(f"[{project.name}] Остановлено пользователем")
                return
            try:
                self._log(f"[{project.name}] {step_name}...")
                step_func()
            except Exception as e:
                import traceback
                error_msg = f"{step_name}: {str(e)}"
                self._log(f"[{project.name}] ❌ Ошибка: {error_msg}")
                project.error_message = error_msg
                project.status = ProjectStatus.ERROR.value
                self._save_projects()
                raise
        
        # Шаги 3-4: ПАРАЛЛЕЛЬНО (изображения + озвучка одновременно!)
        self._log(f"[{project.name}] 🚀 Параллельная генерация: изображения + озвучка")
        self._step_parallel_media(project, project_dir)
        
        # Шаги 5-7: последовательно
        final_steps = [
            ("Сборка превью", lambda: self._step_assemble_preview(project, project_dir)),
            ("Генерация SEO", lambda: self._step_generate_seo(project)),
            ("Генерация превью", lambda: self._step_generate_thumbnails(project, project_dir)),
        ]
        
        for step_name, step_func in final_steps:
            if not self.is_running:
                self._log(f"[{project.name}] Остановлено пользователем")
                return
            
            try:
                self._log(f"[{project.name}] {step_name}...")
                step_func()
            except Exception as e:
                import traceback
                error_msg = f"{step_name}: {str(e)}"
                self._log(f"[{project.name}] ❌ Ошибка: {error_msg}")
                self._log(traceback.format_exc())
                project.error_message = error_msg
                project.status = ProjectStatus.ERROR.value
                self._save_projects()
                raise  # Пробрасываем ошибку наверх
        
        # Готов к проверке
        project.status = ProjectStatus.READY_FOR_REVIEW.value
        project.progress = 100
        self._save_projects()
    
    def _step_analyze_competitor(self, project: SmartProject):
        """Анализ конкурента и подбор параметров (с поддержкой preload)"""
        project.status = ProjectStatus.ANALYZING.value
        project.current_step = "Анализ конкурента..."
        project.progress = 5
        self._log(f"[{project.name}] Анализ конкурента: {project.competitor_channel}")
        
        try:
            from .youtube_analyzer import YouTubeAnalyzer
            from .groq_client import GroqClient
            from config import config
            
            # Проверяем есть ли предзагруженные данные
            preloaded = project.user_edits.get('preloaded', {})
            
            if preloaded and 'titles' in preloaded:
                # Используем предзагруженные данные — экономим 10-20 сек!
                self._log(f"[{project.name}] ⚡ Используем предзагруженные данные")
                titles = preloaded['titles']
                descriptions = preloaded['descriptions']
                channel_info = preloaded.get('channel_info')
            else:
                # Загружаем данные канала
                analyzer = YouTubeAnalyzer(config.api.youtube_keys)
                channel_info = analyzer.get_channel_info(project.competitor_channel)
                
                if not channel_info:
                    self._step_set_defaults(project)
                    return
                
                videos = analyzer.get_channel_videos(channel_info.id, max_results=15)
                titles = [v.title for v in videos]
                descriptions = [v.description for v in videos if v.description]
            
            # СОХРАНЯЕМ данные конкурента для анализа крючков
            project.user_edits['competitor_titles'] = titles
            project.user_edits['competitor_descriptions'] = descriptions[:10]
            self._log(f"[{project.name}] Сохранено {len(titles)} заголовков для анализа крючков")
            
            # AI анализ стиля
            groq = GroqClient(config.api.groq_key, config.api.groq_model)
            style_analysis = groq.analyze_style(descriptions, titles)
            
            # Применяем результаты
            project.ai_style = style_analysis.get('narrative_style', 'Документальный')
            project.ai_voice = self._map_voice(style_analysis.get('recommended_voice', {}))
            project.ai_image_style = self._determine_image_style(project.topic, style_analysis)
            project.ai_transitions = self._determine_transitions(style_analysis)
            project.ai_effects = self._determine_effects(style_analysis)
            project.ai_music_mood = self._determine_music_mood(project.topic, style_analysis)
            
            # Очищаем preloaded данные
            if 'preloaded' in project.user_edits:
                del project.user_edits['preloaded']
                
        except Exception as e:
            self._log(f"Ошибка анализа: {e}, используем defaults")
            self._step_set_defaults(project)
    
    def _step_set_defaults(self, project: SmartProject):
        """Установка параметров по умолчанию"""
        project.ai_style = "Документальный, драматичный"
        project.ai_voice = "Brian (мужской, нарратор)"
        project.ai_image_style = "cinematic, dramatic lighting, 8k, hyperrealistic"
        project.ai_transitions = ["fade", "dissolve", "crossfade"]
        project.ai_effects = {"zoom": 1.05, "pan": True}
        project.ai_music_mood = "epic, dramatic"
    
    def _step_generate_script(self, project: SmartProject):
        """Генерация сценария с мощным крючком"""
        project.status = ProjectStatus.SCRIPTING.value
        project.current_step = "Генерация сценария..."
        project.progress = 15
        self._log(f"[{project.name}] Генерация сценария с анализом крючков")
        
        from .groq_client import GroqClient
        from config import config
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        # Если есть данные о конкуренте — анализируем крючки
        hook_templates = []
        if project.competitor_channel and hasattr(project, 'user_edits'):
            competitor_titles = project.user_edits.get('competitor_titles', [])
            competitor_descriptions = project.user_edits.get('competitor_descriptions', [])
            
            if competitor_titles:
                self._log(f"[{project.name}] Анализ крючков конкурента...")
                project.current_step = "Анализ крючков..."
                
                try:
                    hooks_analysis = groq.analyze_hooks(competitor_titles, competitor_descriptions)
                    hook_templates = hooks_analysis.get('templates', [])
                    self._log(f"[{project.name}] Найдено {len(hook_templates)} шаблонов крючков")
                except Exception as e:
                    self._log(f"[{project.name}] Ошибка анализа крючков: {e}")
        
        # Генерируем сценарий
        project.current_step = "Генерация сценария..."
        script = groq.generate_script(
            topic=project.topic,
            duration=project.duration,
            style=project.ai_style
        )
        
        # Если есть шаблоны крючков — генерируем мощный hook и заменяем начало
        if hook_templates:
            try:
                self._log(f"[{project.name}] Генерация мощного крючка...")
                hook = groq.generate_hook(project.topic, hook_templates, project.ai_style)
                
                # Заменяем стандартный hook на сгенерированный
                if "[HOOK" in script:
                    import re
                    # Находим секцию HOOK и заменяем её содержимое
                    script = re.sub(
                        r'\[HOOK[^\]]*\][^\[]*(?=\[ГЛАВА|\[CHAPTER|$)',
                        f"[HOOK - 0:00-0:45]\n{hook}\n\n",
                        script,
                        count=1
                    )
                    self._log(f"[{project.name}] ✅ Крючок интегрирован в сценарий")
            except Exception as e:
                self._log(f"[{project.name}] Ошибка генерации крючка: {e}")
        
        project.script = script
        project.progress = 30
        self._save_projects()
    
    def _step_generate_images(self, project: SmartProject, project_dir: Path):
        """Генерация изображений через FLUX (ПАРАЛЛЕЛЬНО!)"""
        project.status = ProjectStatus.GENERATING_IMAGES.value
        project.current_step = "Генерация изображений (FLUX)..."
        project.progress = 35
        self._log(f"[{project.name}] 🚀 Параллельная генерация изображений через FLUX")
        
        from .groq_client import GroqClient
        from .flux_generator import FluxGenerator
        from config import config
        
        # Генерация промптов через BATCH запрос (быстрее!)
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        # Определяем длительность для расчёта количества изображений
        duration_map = {
            "10-20 минут": 15,
            "20-30 минут": 25,
            "30-40 минут": 35,
            "40-50 минут": 45,
            "50-60 минут": 55,
            "60+ минут": 65
        }
        duration_minutes = duration_map.get(project.duration, 25)
        
        # Используем batch генерацию промптов
        prompts = groq.generate_image_prompts_batch(
            project.script, 
            project.ai_image_style,
            duration_minutes=duration_minutes
        )
        project.image_prompts = prompts
        
        # Генерация изображений через FLUX
        images_dir = project_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Получаем токены HuggingFace
        hf_tokens = getattr(config.api, 'huggingface_tokens', [])
        generator = FluxGenerator(hf_tokens=hf_tokens, output_dir=images_dir)
        
        # Подготавливаем промпты с улучшениями
        enhanced_prompts = []
        for prompt_data in prompts:
            prompt = prompt_data.get('prompt_en', str(prompt_data)) if isinstance(prompt_data, dict) else str(prompt_data)
            enhanced = self._enhance_military_prompt(prompt, project.ai_image_style)
            enhanced_prompts.append(enhanced)
        
        total = len(enhanced_prompts)
        self._log(f"[{project.name}] Генерация {total} изображений параллельно...")
        
        # Callback для обновления прогресса
        def on_progress(completed, total_count, result):
            project.current_step = f"FLUX: {completed}/{total_count} изображений"
            project.progress = 35 + int(30 * completed / total_count)
            self._save_projects()
            
            if result and result.success:
                self._log(f"  ✅ #{completed}: {result.generation_time:.1f}с")
            elif result:
                self._log(f"  ❌ #{completed}: {result.error[:50]}")
        
        # ПАРАЛЛЕЛЬНАЯ генерация (4-8 потоков в зависимости от токенов)
        max_workers = min(8, len(hf_tokens)) if hf_tokens else 1
        
        results = generator.generate_parallel(
            prompts=enhanced_prompts,
            base_filename="scene",
            max_workers=max_workers,
            on_progress=on_progress
        )
        
        # Собираем успешные результаты
        for result in results:
            if result and result.success and result.path:
                project.images.append(str(result.path))
        
        success_count = len(project.images)
        self._log(f"[{project.name}] ✅ Сгенерировано {success_count}/{total} изображений")
        
        self._save_projects()
    
    def _step_parallel_media(self, project: SmartProject, project_dir: Path):
        """
        ПАРАЛЛЕЛЬНАЯ генерация изображений и озвучки
        
        Запускает оба процесса одновременно — экономит 30-50% времени!
        """
        import concurrent.futures
        
        project.current_step = "Параллельная генерация медиа..."
        project.progress = 35
        
        # Создаём executor для параллельного выполнения
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Запускаем оба процесса
            future_images = executor.submit(self._step_generate_images, project, project_dir)
            future_voice = executor.submit(self._step_generate_voice, project, project_dir)
            
            # Ждём завершения обоих
            errors = []
            
            try:
                future_images.result()
            except Exception as e:
                errors.append(f"Изображения: {e}")
            
            try:
                future_voice.result()
            except Exception as e:
                errors.append(f"Озвучка: {e}")
            
            if errors:
                raise Exception("; ".join(errors))
        
        self._log(f"[{project.name}] ✅ Параллельная генерация завершена")
    
    def _enhance_military_prompt(self, prompt: str, style: str, use_bw: bool = True) -> str:
        """
        Улучшение промпта для военной тематики
        
        Args:
            prompt: Исходный промпт
            style: Стиль изображения
            use_bw: Использовать Ч/Б стиль (как у топовых конкурентов)
        """
        enhancements = []
        prompt_lower = prompt.lower()
        
        # Ч/Б стиль для аутентичности (как у конкурентов)
        if use_bw:
            bw_style = [
                "black and white photograph",
                "vintage 1940s documentary style",
                "authentic wartime photography",
                "grainy film texture",
                "high contrast monochrome",
                "historical archive photograph"
            ]
            enhancements.extend(bw_style)
        else:
            # Цветной стиль
            if "photograph" not in prompt_lower:
                enhancements.append("authentic documentary photograph")
            enhancements.append("Kodachrome film style")
        
        # Качество
        if "detailed" not in prompt_lower:
            enhancements.append("extremely detailed")
        if "realistic" not in prompt_lower:
            enhancements.append("photorealistic")
        
        # Лица — важно для военной тематики
        if "face" not in prompt_lower and any(w in prompt_lower for w in ["soldier", "general", "commander", "person", "man", "woman"]):
            enhancements.append("detailed realistic faces, natural expressions")
        
        # Атмосфера
        atmosphere = [
            "dramatic lighting",
            "cinematic composition",
            "historical accuracy",
            "authentic military equipment"
        ]
        enhancements.extend(atmosphere)
        
        # Техническое качество
        tech_quality = "sharp focus, 8k resolution, professional photography"
        
        return f"{prompt}, {', '.join(enhancements)}, {tech_quality}"
    
    def _step_generate_voice(self, project: SmartProject, project_dir: Path):
        """Генерация озвучки (ПАРАЛЛЕЛЬНО с несколькими ключами!)"""
        project.status = ProjectStatus.GENERATING_VOICE.value
        project.current_step = "Генерация озвучки..."
        project.progress = 70
        self._log(f"[{project.name}] 🚀 Параллельная генерация озвучки")
        
        from .elevenlabs_client import ElevenLabsClient
        from config import config
        
        if not config.api.elevenlabs_keys:
            self._log("ElevenLabs ключи не настроены, пропускаем озвучку")
            return
        
        audio_dir = project_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        
        client = ElevenLabsClient(api_keys=config.api.elevenlabs_keys)
        voice_id = self._get_voice_id(project.ai_voice)
        
        # Определяем язык для нормализации текста
        language_map = {
            "Русский": "ru",
            "English": "en",
            "Español": "es",
            "Deutsch": "de",
            "Français": "fr",
            "Português": "pt",
            "Italiano": "it"
        }
        lang_code = language_map.get(project.language, "ru")
        
        # Используем параллельную генерацию если есть несколько ключей
        num_keys = len(config.api.elevenlabs_keys)
        
        if num_keys >= 2:
            self._log(f"  Используем {num_keys} ключей параллельно")
            audio_path = client.generate_voiceover_parallel(
                script=project.script,
                voice_id=voice_id,
                output_dir=audio_dir,
                max_workers=min(3, num_keys),
                language=lang_code
            )
        else:
            # Обычная генерация с одним ключом
            audio_path = client.text_to_speech(
                project.script,
                voice_id,
                audio_dir / "voiceover.mp3",
                language=lang_code
            )
        
        if audio_path:
            project.audio_path = str(audio_path)
            self._log(f"  ✅ Озвучка готова: {audio_path}")
        
        project.progress = 85
        self._save_projects()
    
    def _step_assemble_preview(self, project: SmartProject, project_dir: Path):
        """Сборка БЫСТРОГО превью видео для проверки"""
        project.status = ProjectStatus.ASSEMBLING.value
        project.current_step = "Сборка быстрого превью..."
        project.progress = 90
        self._log(f"[{project.name}] 🎬 Сборка быстрого превью (720p)")
        
        # Сохраняем данные для финального рендера
        preview_data = {
            "images": project.images,
            "audio": project.audio_path,
            "transitions": project.ai_transitions,
            "effects": project.ai_effects,
            "music_mood": project.ai_music_mood
        }
        
        data_path = project_dir / "preview_data.json"
        data_path.write_text(json.dumps(preview_data, ensure_ascii=False, indent=2))
        
        # Генерируем БЫСТРОЕ превью для проверки (720p, без эффектов)
        try:
            from .video_editor import VideoEditor
            
            images = [Path(p) for p in project.images if Path(p).exists()]
            if images and project.audio_path and Path(project.audio_path).exists():
                editor = VideoEditor()
                preview_path = project_dir / "quick_preview.mp4"
                
                editor.create_quick_preview(
                    images=images,
                    output_path=preview_path,
                    audio_path=Path(project.audio_path),
                    resolution=(1280, 720)
                )
                
                project.preview_video = str(preview_path)
                self._log(f"[{project.name}] ✅ Быстрое превью готово: {preview_path}")
            else:
                project.preview_video = str(data_path)
                self._log(f"[{project.name}] ⚠️ Недостаточно данных для превью")
        except Exception as e:
            self._log(f"[{project.name}] ⚠️ Ошибка превью: {e}, сохраняем данные")
            project.preview_video = str(data_path)
    
    def _step_generate_seo(self, project: SmartProject):
        """Генерация SEO с хештегами и A/B заголовками"""
        project.current_step = "Генерация SEO..."
        project.progress = 92
        
        from .groq_client import GroqClient
        from config import config
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        seo = groq.generate_seo(
            project.name, 
            project.script, 
            [],
            subniche=project.sub_niche
        )
        
        # Заголовок и альтернативы для A/B теста
        alt_titles = seo.get('seo_title_alternatives', [])
        project.seo_title = alt_titles[0] if alt_titles else project.name
        project.seo_alt_titles = alt_titles
        
        # Описание
        project.seo_description = seo.get('description', '')
        
        # Теги
        project.seo_tags = seo.get('tags', [])
        
        # Хештеги
        project.seo_hashtags = seo.get('hashtags', [])
        
        # Текст для закреплённого комментария
        project.seo_first_comment = seo.get('first_comment', '')
        
        self._log(f"  SEO: {len(project.seo_tags)} тегов, {len(project.seo_hashtags)} хештегов, {len(project.seo_alt_titles)} заголовков")
    
    def _step_generate_thumbnails(self, project: SmartProject, project_dir: Path):
        """
        Генерация 3 ВИРУСНЫХ превью для A/B теста
        
        Этапы:
        1. AI анализ темы и целевой аудитории
        2. Генерация 3 уникальных концепций (разные триггеры)
        3. Создание детальных промптов
        4. Генерация изображений
        5. Сохранение промптов для редактирования
        """
        project.current_step = "Анализ для превью..."
        project.progress = 95
        self._log(f"[{project.name}] 🎨 Генерация 3 вирусных превью")
        
        from .flux_generator import FluxGenerator
        from .groq_client import GroqClient
        from config import config
        
        thumbnails_dir = project_dir / "thumbnails"
        thumbnails_dir.mkdir(exist_ok=True)
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        # === ГЛУБОКИЙ АНАЛИЗ ДЛЯ ПРЕВЬЮ ===
        self._log(f"[{project.name}] Анализ для создания вирусных превью...")
        
        thumbnail_analysis = groq.generate_viral_thumbnail_concepts(
            topic=project.topic,
            title=project.seo_title or project.name,
            script_summary=project.script[:2000] if project.script else "",
            style=project.ai_style
        )
        
        # Получаем 3 концепции
        concepts = thumbnail_analysis.get('concepts', [])
        
        if not concepts or len(concepts) < 3:
            # Fallback если AI не вернул концепции
            concepts = [
                {
                    "type": "dramatic",
                    "prompt_en": f"dramatic cinematic scene, {project.topic}, intense atmosphere, dark moody lighting, epic composition, war photography style, 8k, photorealistic, youtube thumbnail",
                    "why_viral": "Драматичность привлекает внимание"
                },
                {
                    "type": "emotional",
                    "prompt_en": f"emotional powerful moment, {project.topic}, human face with intense expression, cinematic lighting, documentary style, 8k, photorealistic, youtube thumbnail",
                    "why_viral": "Эмоции вызывают эмпатию"
                },
                {
                    "type": "mystery",
                    "prompt_en": f"mysterious intriguing scene, {project.topic}, shadows and light, hidden secrets revealed, cinematic composition, 8k, photorealistic, youtube thumbnail",
                    "why_viral": "Загадка вызывает любопытство"
                }
            ]
        
        # Получаем токены
        hf_tokens = getattr(config.api, 'huggingface_tokens', [])
        generator = FluxGenerator(hf_tokens=hf_tokens, output_dir=thumbnails_dir)
        
        project.thumbnails = []
        thumbnail_prompts = []  # Сохраняем промпты
        
        for i, concept in enumerate(concepts[:3]):
            concept_type = concept.get('type', f'variant_{i+1}')
            prompt_en = concept.get('prompt_en', '')
            why_viral = concept.get('why_viral', '')
            
            project.current_step = f"Превью {i+1}/3: {concept_type}"
            self._log(f"[{project.name}] Генерация превью #{i+1}: {concept_type}")
            
            # Улучшаем промпт техническими тегами
            enhanced_prompt = self._enhance_thumbnail_prompt(prompt_en)
            
            result = generator.generate(
                prompt=enhanced_prompt,
                filename=f"thumbnail_{i+1}_{concept_type}",
                width=1280,
                height=720,
                steps=30,  # Больше шагов для качества
                guidance=4.5
            )
            
            if result.success and result.path:
                project.thumbnails.append(str(result.path))
                
                # Сохраняем промпт рядом с изображением
                prompt_file = result.path.with_suffix('.txt')
                prompt_data = f"""=== THUMBNAIL #{i+1}: {concept_type.upper()} ===

PROMPT (English):
{enhanced_prompt}

WHY VIRAL:
{why_viral}

ORIGINAL CONCEPT:
{prompt_en}

---
Для перегенерации: скопируй PROMPT и измени по необходимости
"""
                prompt_file.write_text(prompt_data, encoding='utf-8')
                thumbnail_prompts.append({
                    'type': concept_type,
                    'prompt': enhanced_prompt,
                    'why_viral': why_viral,
                    'path': str(result.path)
                })
                
                self._log(f"  ✅ Превью {concept_type}: готово + промпт сохранён")
            else:
                self._log(f"  ❌ Превью {concept_type}: ошибка генерации")
            
            time.sleep(2)
        
        # Сохраняем все промпты в один файл для удобства
        all_prompts_file = thumbnails_dir / "ALL_PROMPTS.txt"
        all_prompts_content = f"""=== ПРОМПТЫ ДЛЯ ПРЕВЬЮ: {project.name} ===
Тема: {project.topic}
Заголовок: {project.seo_title or project.name}

"""
        for i, tp in enumerate(thumbnail_prompts, 1):
            all_prompts_content += f"""
{'='*50}
ВАРИАНТ #{i}: {tp['type'].upper()}
{'='*50}

PROMPT:
{tp['prompt']}

ПОЧЕМУ ВИРУСНЫЙ:
{tp['why_viral']}

ФАЙЛ: {tp['path']}

"""
        all_prompts_file.write_text(all_prompts_content, encoding='utf-8')
        
        # Сохраняем промпты в проект для доступа из UI
        project.thumbnail_prompts = thumbnail_prompts
        
        self._log(f"[{project.name}] ✅ {len(project.thumbnails)} превью готовы, промпты сохранены")
        self._save_projects()
    
    def _enhance_thumbnail_prompt(self, prompt: str) -> str:
        """Улучшение промпта для thumbnail техническими тегами"""
        # Базовые улучшения для YouTube превью
        enhancements = [
            "youtube thumbnail style",
            "eye-catching composition",
            "vibrant saturated colors",
            "high contrast",
            "sharp focus",
            "professional photography",
            "8k ultra detailed",
            "cinematic lighting"
        ]
        
        # Проверяем что уже есть в промпте
        prompt_lower = prompt.lower()
        missing = [e for e in enhancements if e.lower() not in prompt_lower]
        
        if missing:
            return f"{prompt}, {', '.join(missing[:5])}"
        return prompt
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _map_voice(self, voice_info: dict) -> str:
        """Маппинг рекомендации голоса на реальный голос"""
        gender = voice_info.get('gender', 'мужской').lower()
        if 'женск' in gender:
            return "Rachel (женский, спокойный)"
        return "Brian (мужской, нарратор)"
    
    def _determine_image_style(self, topic: str, style: dict) -> str:
        """Определение стиля изображений по теме"""
        topic_lower = topic.lower()
        
        if any(w in topic_lower for w in ['война', 'военн', 'ww2', 'битва', 'сражен']):
            return "war photography, dramatic, gritty, cinematic, 8k, hyperrealistic"
        elif any(w in topic_lower for w in ['истори', 'древн', 'средневеков']):
            return "historical, documentary style, cinematic lighting, detailed, 8k"
        elif any(w in topic_lower for w in ['космос', 'планет', 'галакти']):
            return "space, sci-fi, epic, cinematic, 8k, detailed"
        elif any(w in topic_lower for w in ['природ', 'животн', 'океан']):
            return "nature documentary, cinematic, 8k, beautiful lighting"
        else:
            return "cinematic, dramatic lighting, 8k, hyperrealistic, detailed"
    
    def _determine_transitions(self, style: dict) -> List[str]:
        """Определение переходов"""
        return ["fade", "dissolve", "crossfade", "slide_left"]
    
    def _determine_effects(self, style: dict) -> dict:
        """Определение эффектов"""
        return {
            "zoom": 1.05,
            "pan": True,
            "color_correction": "cinematic"
        }
    
    def _determine_music_mood(self, topic: str, style: dict) -> str:
        """Определение настроения музыки"""
        topic_lower = topic.lower()
        
        if any(w in topic_lower for w in ['война', 'битва', 'сражен']):
            return "epic, dramatic, orchestral"
        elif any(w in topic_lower for w in ['тайн', 'загадк', 'мистер']):
            return "mysterious, suspenseful, ambient"
        elif any(w in topic_lower for w in ['ужас', 'страш']):
            return "dark, horror, tense"
        else:
            return "cinematic, emotional, orchestral"
    
    def _get_voice_id(self, voice_name: str) -> str:
        """Получение ID голоса по имени"""
        voices = {
            "Brian (мужской, нарратор)": "nPczCjzI2devNBz1zQrb",
            "Rachel (женский, спокойный)": "21m00Tcm4TlvDq8ikWAM",
            "Adam (мужской, глубокий)": "pNInz6obpgDQGcFmaJgB",
            "Clyde (мужской, военный)": "2EiwWnXFnvU5JabPnv8n",
        }
        return voices.get(voice_name, "nPczCjzI2devNBz1zQrb")
    
    # === МЕТОДЫ ДЛЯ ПРАВОК ===
    
    def apply_edit(self, project_id: str, edit_type: str, edit_data: dict):
        """Применение правки пользователя"""
        if project_id not in self.projects:
            return
        
        project = self.projects[project_id]
        
        if edit_type == "replace_image":
            # Замена изображения
            index = edit_data.get('index')
            new_prompt = edit_data.get('prompt')
            if index is not None and new_prompt:
                project.user_edits[f"image_{index}"] = new_prompt
        
        elif edit_type == "change_transition":
            project.ai_transitions = edit_data.get('transitions', project.ai_transitions)
        
        elif edit_type == "change_effects":
            project.ai_effects.update(edit_data.get('effects', {}))
        
        elif edit_type == "edit_script":
            project.script = edit_data.get('script', project.script)
        
        self._save_projects()
    
    def render_final(self, project_id: str, on_progress: Callable = None, 
                     add_subtitles: bool = False) -> Optional[str]:
        """
        Финальный рендер проекта
        
        Собирает видео из:
        - Изображений с Ken Burns эффектом
        - Озвучки
        - Фоновой музыки (если выбрана)
        - Субтитров (опционально)
        
        Args:
            project_id: ID проекта
            on_progress: Callback для прогресса
            add_subtitles: Добавить субтитры к видео
        """
        if project_id not in self.projects:
            return None
        
        project = self.projects[project_id]
        project.status = ProjectStatus.RENDERING.value
        project.current_step = "Подготовка к рендеру..."
        project.progress = 0
        self._save_projects()
        
        try:
            from .video_editor import VideoEditor, VideoConfig, SceneConfig, SubtitleStyle, generate_subtitles_from_script
            from .quality_checker import QualityChecker
            from pathlib import Path
            
            # Проверка качества перед рендером
            checker = QualityChecker()
            report = checker.check_project(project)
            
            if not report.passed:
                project.error_message = f"Проверка не пройдена: {report.summary}"
                project.status = ProjectStatus.ERROR.value
                self._save_projects()
                return None
            
            project.current_step = "Настройка видео..."
            project.progress = 10
            
            # Настройка видеоредактора
            config = VideoConfig(
                resolution=(1920, 1080),
                fps=30,
                enable_zoom=True,
                min_zoom=1.0,
                max_zoom=1.15,
                transition_type=project.ai_transitions[0] if project.ai_transitions else "fade",
                transition_duration=0.5,
                color_grade="cinematic"
            )
            
            editor = VideoEditor(config)
            
            # Подготовка сцен
            project.current_step = "Расчёт таймингов..."
            project.progress = 20
            
            from moviepy import AudioFileClip
            audio = AudioFileClip(project.audio_path)
            total_duration = audio.duration
            audio.close()
            
            # Рассчитываем длительность каждой сцены
            images = [Path(p) for p in project.images if Path(p).exists()]
            if not images:
                raise Exception("Нет изображений для рендера")
            
            scene_duration = total_duration / len(images)
            
            scenes = []
            current_time = 0
            
            for i, img_path in enumerate(images):
                scenes.append(SceneConfig(
                    image_path=img_path,
                    duration=scene_duration,
                    start_time=current_time,
                    zoom_direction="in" if i % 2 == 0 else "out"
                ))
                current_time += scene_duration
            
            project.current_step = f"Рендер видео ({len(scenes)} сцен)..."
            project.progress = 30
            self._save_projects()
            
            # Путь для выходного файла
            project_dir = self.output_dir / project_id
            output_path = project_dir / f"{project.name.replace(' ', '_')}_final.mp4"
            
            # Ищем фоновую музыку
            music_path = self._find_music(project.ai_music_mood)
            
            # Рендерим базовое видео
            editor.create_video(
                scenes=scenes,
                audio_path=Path(project.audio_path),
                output_path=output_path,
                music_path=music_path,
                music_volume=0.12
            )
            
            # Добавляем субтитры если нужно
            if add_subtitles and project.script:
                project.current_step = "Добавление субтитров..."
                project.progress = 85
                self._save_projects()
                
                try:
                    self._log(f"[{project.name}] 📝 Генерация субтитров...")
                    
                    # Генерируем субтитры из сценария
                    subtitles = generate_subtitles_from_script(project.script, total_duration)
                    
                    if subtitles:
                        # Стиль субтитров
                        subtitle_style = SubtitleStyle(
                            font="Arial-Bold",
                            font_size=48,
                            color="white",
                            stroke_color="black",
                            stroke_width=3,
                            position="bottom",
                            margin_bottom=80
                        )
                        
                        # Путь для видео с субтитрами
                        subtitled_path = project_dir / f"{project.name.replace(' ', '_')}_subtitled.mp4"
                        
                        editor.add_subtitles_to_video(
                            video_path=output_path,
                            subtitles=subtitles,
                            output_path=subtitled_path,
                            style=subtitle_style
                        )
                        
                        # Заменяем основной файл на версию с субтитрами
                        output_path.unlink()
                        subtitled_path.rename(output_path)
                        
                        self._log(f"[{project.name}] ✅ Субтитры добавлены ({len(subtitles)} фраз)")
                except Exception as e:
                    self._log(f"[{project.name}] ⚠️ Ошибка субтитров: {e}, видео без субтитров")
            
            project.final_video = str(output_path)
            project.status = ProjectStatus.COMPLETED.value
            project.progress = 100
            project.current_step = "Готово!"
            self._save_projects()
            
            self._log(f"✅ Рендер завершён: {output_path}")
            return str(output_path)
            
        except Exception as e:
            project.status = ProjectStatus.ERROR.value
            project.error_message = str(e)
            project.current_step = f"Ошибка: {e}"
            self._save_projects()
            self._log(f"❌ Ошибка рендера: {e}")
            return None
    
    def _find_music(self, mood: str) -> Optional[Path]:
        """Поиск фоновой музыки по настроению"""
        music_dir = Path("video_factory/data/music")
        if not music_dir.exists():
            music_dir = self.output_dir / "music"
        
        if not music_dir.exists():
            return None
        
        # Ищем подходящую музыку
        mood_lower = mood.lower() if mood else ""
        
        for mp3 in music_dir.glob("*.mp3"):
            name_lower = mp3.stem.lower()
            # Простой матчинг по ключевым словам
            if any(word in name_lower for word in mood_lower.split()):
                return mp3
        
        # Если не нашли по настроению — берём первую
        mp3_files = list(music_dir.glob("*.mp3"))
        return mp3_files[0] if mp3_files else None
    
    def generate_subtitles_file(self, project_id: str) -> Optional[str]:
        """
        Генерация SRT файла субтитров для проекта
        
        Создаёт .srt файл который можно:
        - Загрузить на YouTube отдельно
        - Использовать в любом видеоплеере
        - Редактировать вручную
        
        Returns:
            Путь к SRT файлу или None
        """
        if project_id not in self.projects:
            return None
        
        project = self.projects[project_id]
        
        if not project.script or not project.audio_path:
            self._log(f"[{project.name}] Нет сценария или аудио для субтитров")
            return None
        
        try:
            from .video_editor import generate_subtitles_from_script
            from moviepy import AudioFileClip
            
            # Получаем длительность аудио
            audio = AudioFileClip(project.audio_path)
            total_duration = audio.duration
            audio.close()
            
            # Генерируем субтитры
            subtitles = generate_subtitles_from_script(project.script, total_duration)
            
            if not subtitles:
                return None
            
            # Создаём SRT файл
            project_dir = self.output_dir / project_id
            srt_path = project_dir / f"{project.name.replace(' ', '_')}.srt"
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, sub in enumerate(subtitles, 1):
                    start = self._format_srt_time(sub['start'])
                    end = self._format_srt_time(sub['end'])
                    text = sub['text']
                    
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
            
            self._log(f"[{project.name}] ✅ SRT файл создан: {srt_path}")
            return str(srt_path)
            
        except Exception as e:
            self._log(f"[{project.name}] ❌ Ошибка генерации SRT: {e}")
            return None
    
    def _format_srt_time(self, seconds: float) -> str:
        """Форматирование времени для SRT (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def get_project(self, project_id: str) -> Optional[SmartProject]:
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> List[SmartProject]:
        return list(self.projects.values())
    
    def get_ready_projects(self) -> List[SmartProject]:
        """Проекты готовые к проверке"""
        return [p for p in self.projects.values() if p.status == ProjectStatus.READY_FOR_REVIEW.value]
    
    def get_queue_status(self) -> dict:
        """Статус очереди"""
        return {
            "is_running": self.is_running,
            "queue_length": len(self.queue),
            "current_project": self.current_project_id,
            "projects_in_queue": self.queue.copy()
        }
