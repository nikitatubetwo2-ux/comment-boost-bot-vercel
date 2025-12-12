# Core модули Video Factory

from .youtube_analyzer import YouTubeAnalyzer, ChannelInfo, VideoInfo
from .groq_client import GroqClient
from .channel_profile import ChannelProfile, ProfileManager
from .elevenlabs_client import ElevenLabsClient, Voice
from .image_generator import ImageGenerator, ImageResult
from .video_editor import VideoEditor, VideoConfig, SceneConfig
from .srt_generator import SRTGenerator
from .copyright_checker import CopyrightChecker, CopyrightStatus
from .project_manager import ProjectManager, VideoProject, ProjectStage
from .youtube_music import YouTubeAudioLibrary, AudioTrack
from .retention_analyzer import RetentionAnalyzer, VideoStructure
from .seo_optimizer import SEOOptimizer, SEOResult
from .script_parser import ScriptParser, Scene
from .batch_processor import BatchProcessor, VideoTask, TaskStatus
from .exporter import ProjectExporter, ExportResult
from .pipeline import VideoPipeline, PipelineResult
from .smart_pipeline import SmartPipeline, SmartProject, ProjectStatus
from .channel_style import ChannelStyle, ChannelStyleManager
from .thumbnail_generator import ThumbnailGenerator, ThumbnailResult, TrendAnalyzer
from .quality_checker import QualityChecker, QualityReport, QualityIssue

__all__ = [
    # YouTube
    'YouTubeAnalyzer', 'ChannelInfo', 'VideoInfo',
    'YouTubeAudioLibrary', 'AudioTrack',
    
    # AI
    'GroqClient',
    
    # Профили
    'ChannelProfile', 'ProfileManager',
    
    # Озвучка
    'ElevenLabsClient', 'Voice',
    
    # Изображения
    'ImageGenerator', 'ImageResult',
    
    # Видео
    'VideoEditor', 'VideoConfig', 'SceneConfig',
    'SRTGenerator',
    
    # Анализ
    'RetentionAnalyzer', 'VideoStructure',
    'SEOOptimizer', 'SEOResult',
    'CopyrightChecker', 'CopyrightStatus',
    
    # Сценарий
    'ScriptParser', 'Scene',
    
    # Проекты
    'ProjectManager', 'VideoProject', 'ProjectStage',
    'BatchProcessor', 'VideoTask', 'TaskStatus',
    'ProjectExporter', 'ExportResult',
    
    # Pipeline
    'VideoPipeline', 'PipelineResult',
    'SmartPipeline', 'SmartProject', 'ProjectStatus',
    
    # Профили каналов
    'ChannelStyle', 'ChannelStyleManager',
    
    # Превью и тренды
    'ThumbnailGenerator', 'ThumbnailResult', 'TrendAnalyzer',
    
    # Контроль качества
    'QualityChecker', 'QualityReport', 'QualityIssue',
]
