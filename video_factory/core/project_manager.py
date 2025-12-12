"""
Менеджер проекта — связывает все модули вместе
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum

from .youtube_analyzer import YouTubeAnalyzer, ChannelInfo, VideoInfo
from .groq_client import GroqClient
from .channel_profile import ChannelProfile, ProfileManager
from .elevenlabs_client import ElevenLabsClient
from .image_generator import ImageGenerator
from .video_editor import VideoEditor, VideoConfig, SceneConfig
from .srt_generator import SRTGenerator
from .copyright_checker import CopyrightChecker


class ProjectStage(Enum):
    """Этапы проекта"""
    CREATED = "created"
    ANALYZED = "analyzed"
    SCRIPT_READY = "script_ready"
    IMAGES_READY = "images_ready"
    VOICE_READY = "voice_ready"
    RENDERED = "rendered"
    COMPLETED = "completed"


@dataclass
class VideoProject:
    """Проект видео"""
    
    # Идентификация
    id: str
    name: str
    created_at: str = ""
    updated_at: str = ""
    
    # Статус
    stage: str = "created"
    progress: int = 0
    
    # Профиль канала
    profile_path: str = ""
    
    # Контент
    topic: str = ""
    title: str = ""
    duration: str = "20-30 минут"
    style: str = "Документальный"
    
    # Сценарий
    script: str = ""
    script_word_count: int = 0
    
    # Превью
    preview_prompts: List[Dict] = field(default_factory=list)
    
    # Изображения
    image_prompts: List[Dict] = field(default_factory=list)
    image_paths: List[str] = field(default_factory=list)
    
    # Озвучка
    voice_id: str = ""
    voice_name: str = ""
    audio_path: str = ""
    
    # Музыка
    music_path: str = ""
    music_title: str = ""
    music_volume: float = 0.15
    
    # SEO
    seo_description: str = ""
    seo_tags: List[str] = field(default_factory=list)
    seo_hashtags: List[str] = field(default_factory=list)
    
    # Выходные файлы
    output_video: str = ""
    output_srt: str = ""
    output_thumbnail: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "VideoProject":
        return cls(**data)
    
    def save(self, path: Path):
        """Сохранение проекта"""
        self.updated_at = datetime.now().isoformat()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path) -> "VideoProject":
        """Загрузка проекта"""
        with open(path, 'r', encoding='utf-8') as f:
            return cls.from_dict(json.load(f))


class ProjectManager:
    """Менеджер проектов"""
    
    def __init__(
        self,
        projects_dir: Path,
        profiles_dir: Path,
        output_dir: Path,
        config: Dict[str, Any]
    ):
        self.projects_dir = projects_dir
        self.profiles_dir = profiles_dir
        self.output_dir = output_dir
        self.config = config
        
        # Создаём директории
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализируем клиенты (лениво)
        self._youtube = None
        self._groq = None
        self._elevenlabs = None
        self._profile_manager = ProfileManager(profiles_dir)
    
    @property
    def youtube(self) -> YouTubeAnalyzer:
        if not self._youtube and self.config.get('youtube_key'):
            self._youtube = YouTubeAnalyzer(self.config['youtube_key'])
        return self._youtube
    
    @property
    def groq(self) -> GroqClient:
        if not self._groq and self.config.get('groq_key'):
            self._groq = GroqClient(
                self.config['groq_key'],
                self.config.get('groq_model', 'llama-3.3-70b-versatile')
            )
        return self._groq
    
    @property
    def elevenlabs(self) -> ElevenLabsClient:
        if not self._elevenlabs and self.config.get('elevenlabs_key'):
            self._elevenlabs = ElevenLabsClient(self.config['elevenlabs_key'])
        return self._elevenlabs
    
    def create_project(self, name: str, topic: str = "") -> VideoProject:
        """Создание нового проекта"""
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        project = VideoProject(
            id=project_id,
            name=name,
            topic=topic
        )
        
        # Создаём папку проекта
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "images").mkdir(exist_ok=True)
        (project_dir / "audio").mkdir(exist_ok=True)
        
        # Сохраняем
        project.save(project_dir / "project.json")
        
        return project
    
    def analyze_competitor(
        self,
        channel_url: str,
        niche: str,
        callback: Callable = None
    ) -> ChannelProfile:
        """Полный анализ конкурента"""
        
        if callback:
            callback("Получение информации о канале...")
        
        # Получаем ID канала
        channel_id = self.youtube.extract_channel_id(channel_url)
        if not channel_id:
            raise ValueError("Не удалось получить ID канала")
        
        # Информация о канале
        channel_info = self.youtube.get_channel_info(channel_id)
        if not channel_info:
            raise ValueError("Не удалось получить информацию о канале")
        
        if callback:
            callback("Загрузка видео канала...")
        
        # Получаем видео
        videos = self.youtube.get_channel_videos(channel_id, max_results=30)
        
        if callback:
            callback("Анализ статистики...")
        
        # Статистика
        stats = self.youtube.analyze_channel_stats(videos)
        
        if callback:
            callback("Анализ заголовков (AI)...")
        
        # Анализ заголовков через Groq
        titles = [v.title for v in videos]
        title_analysis = self.groq.analyze_titles(titles)
        
        if callback:
            callback("Анализ стиля (AI)...")
        
        # Анализ стиля
        descriptions = [v.description for v in videos]
        style_analysis = self.groq.analyze_style(descriptions, titles)
        
        if callback:
            callback("Создание профиля...")
        
        # Создаём профиль
        profile = self._profile_manager.create_profile_from_analysis(
            channel_info.to_dict(),
            stats,
            title_analysis,
            style_analysis,
            niche
        )
        
        # Сохраняем
        self._profile_manager.save_profile(profile)
        
        return profile
    
    def generate_content(
        self,
        project: VideoProject,
        profile: ChannelProfile,
        callback: Callable = None
    ) -> VideoProject:
        """Генерация контента для проекта"""
        
        if callback:
            callback("Генерация подниши...")
        
        # Генерируем поднишу
        subniche_result = self.groq.generate_subniche(
            profile.niche,
            profile.get_style_summary()
        )
        
        if callback:
            callback("Генерация тем...")
        
        # Генерируем темы
        topics = self.groq.generate_video_topics(
            subniche_result.get('recommended', profile.niche),
            profile.get_style_summary(),
            count=5
        )
        
        # Берём первую тему (или можно дать выбор)
        if topics:
            project.topic = topics[0].get('title', project.topic)
            project.title = topics[0].get('title', '')
        
        if callback:
            callback("Генерация сценария...")
        
        # Генерируем сценарий
        script = self.groq.generate_script(
            project.title,
            project.duration,
            project.style
        )
        project.script = script
        project.script_word_count = len(script.split())
        
        if callback:
            callback("Генерация промптов для превью...")
        
        # Промпты для превью
        preview_prompts = self.groq.generate_preview_prompts(
            project.title,
            profile.get_style_summary()
        )
        project.preview_prompts = preview_prompts
        
        if callback:
            callback("Генерация промптов для изображений...")
        
        # Промпты для изображений
        image_prompts = self.groq.generate_image_prompts(script, project.style)
        project.image_prompts = image_prompts
        
        if callback:
            callback("Генерация SEO...")
        
        # SEO
        seo = self.groq.generate_seo(
            project.title,
            script,
            profile.top_tags
        )
        project.seo_description = seo.get('description', '')
        project.seo_tags = seo.get('tags', [])
        project.seo_hashtags = seo.get('hashtags', [])
        
        project.stage = ProjectStage.SCRIPT_READY.value
        project.progress = 30
        
        return project
    
    def generate_voice(
        self,
        project: VideoProject,
        voice_id: str,
        callback: Callable = None
    ) -> VideoProject:
        """Генерация озвучки"""
        
        project_dir = self.projects_dir / project.id
        audio_dir = project_dir / "audio"
        
        if callback:
            callback("Генерация озвучки...")
        
        # Генерируем озвучку
        audio_files = self.elevenlabs.generate_full_voiceover(
            project.script,
            voice_id,
            audio_dir
        )
        
        # Объединяем аудио файлы (если несколько)
        if len(audio_files) == 1:
            project.audio_path = str(audio_files[0])
        else:
            # TODO: Объединить через ffmpeg
            project.audio_path = str(audio_files[0])
        
        project.voice_id = voice_id
        project.stage = ProjectStage.VOICE_READY.value
        project.progress = 60
        
        return project
    
    def render_video(
        self,
        project: VideoProject,
        video_config: VideoConfig = None,
        callback: Callable = None
    ) -> VideoProject:
        """Рендер финального видео"""
        
        project_dir = self.projects_dir / project.id
        
        if callback:
            callback("Подготовка к рендеру...")
        
        # Создаём редактор
        editor = VideoEditor(video_config or VideoConfig())
        
        # Собираем изображения
        images = [Path(p) for p in project.image_paths if Path(p).exists()]
        
        if not images:
            raise ValueError("Нет изображений для рендера")
        
        if not project.audio_path or not Path(project.audio_path).exists():
            raise ValueError("Нет аудио для рендера")
        
        if callback:
            callback("Рендер видео...")
        
        # Рендерим
        output_path = self.output_dir / f"{project.id}_{project.name}.mp4"
        
        music_path = Path(project.music_path) if project.music_path else None
        
        editor.create_video_simple(
            images,
            Path(project.audio_path),
            output_path,
            music_path,
            project.music_volume
        )
        
        project.output_video = str(output_path)
        
        if callback:
            callback("Генерация субтитров...")
        
        # Генерируем SRT
        srt_gen = SRTGenerator()
        srt_path = output_path.with_suffix('.srt')
        srt_gen.generate_from_script(project.script, srt_path)
        project.output_srt = str(srt_path)
        
        project.stage = ProjectStage.RENDERED.value
        project.progress = 100
        
        return project
    
    def list_projects(self) -> List[Dict]:
        """Список всех проектов"""
        projects = []
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                project_file = project_dir / "project.json"
                if project_file.exists():
                    try:
                        project = VideoProject.load(project_file)
                        projects.append({
                            'id': project.id,
                            'name': project.name,
                            'stage': project.stage,
                            'progress': project.progress,
                            'updated_at': project.updated_at
                        })
                    except:
                        continue
        
        return sorted(projects, key=lambda x: x['updated_at'], reverse=True)
    
    def load_project(self, project_id: str) -> Optional[VideoProject]:
        """Загрузка проекта"""
        project_file = self.projects_dir / project_id / "project.json"
        if project_file.exists():
            return VideoProject.load(project_file)
        return None
    
    def save_project(self, project: VideoProject):
        """Сохранение проекта"""
        project_dir = self.projects_dir / project.id
        project_dir.mkdir(parents=True, exist_ok=True)
        project.save(project_dir / "project.json")
