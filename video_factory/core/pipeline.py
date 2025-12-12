"""
Pipeline — полный цикл создания видео от анализа до экспорта
"""

from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json

from .youtube_analyzer import YouTubeAnalyzer
from .groq_client import GroqClient
from .channel_profile import ChannelProfile, ProfileManager
from .elevenlabs_client import ElevenLabsClient
from .video_editor import VideoEditor, VideoConfig
from .srt_generator import SRTGenerator
from .seo_optimizer import SEOOptimizer
from .script_parser import ScriptParser
from .copyright_checker import CopyrightChecker
from .exporter import ProjectExporter


@dataclass
class PipelineResult:
    """Результат выполнения pipeline"""
    success: bool
    stage: str
    data: Dict[str, Any]
    error: str = ""


class VideoPipeline:
    """
    Полный pipeline создания видео:
    1. Анализ конкурента → профиль
    2. Генерация идей → темы
    3. Генерация сценария
    4. Генерация промптов для изображений
    5. Озвучка
    6. Монтаж
    7. SEO
    8. Экспорт
    """
    
    def __init__(self, config: Dict[str, Any], output_dir: Path, profiles_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.profiles_dir = profiles_dir
        
        # Создаём директории
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Callbacks для прогресса
        self.on_progress: Optional[Callable] = None
        self.on_stage_complete: Optional[Callable] = None
        
        # Текущий проект
        self.project_data: Dict[str, Any] = {}
    
    def _report_progress(self, stage: str, progress: int, message: str):
        """Отчёт о прогрессе"""
        if self.on_progress:
            self.on_progress(stage, progress, message)
    
    def _init_clients(self):
        """Инициализация API клиентов"""
        self.youtube = YouTubeAnalyzer(api_keys=self.config.get('youtube_keys', []))
        self.groq = GroqClient(
            self.config.get('groq_key', ''),
            self.config.get('groq_model', 'llama-3.3-70b-versatile')
        )
        self.elevenlabs = ElevenLabsClient(api_keys=self.config.get('elevenlabs_keys', []))
        self.profile_manager = ProfileManager(self.profiles_dir)
        self.seo = SEOOptimizer()
        self.script_parser = ScriptParser()
    
    def analyze_competitor(self, channel_url: str, niche: str) -> PipelineResult:
        """Этап 1: Анализ конкурента"""
        try:
            self._report_progress("analyze", 0, "Получение информации о канале...")
            
            # Получаем ID канала
            channel_id = self.youtube.extract_channel_id(channel_url)
            if not channel_id:
                return PipelineResult(False, "analyze", {}, "Не удалось получить ID канала")
            
            self._report_progress("analyze", 20, "Загрузка видео...")
            channel_info = self.youtube.get_channel_info(channel_id)
            videos = self.youtube.get_channel_videos(channel_id, max_results=30)
            
            self._report_progress("analyze", 40, "Анализ статистики...")
            stats = self.youtube.analyze_channel_stats(videos)
            
            self._report_progress("analyze", 60, "AI анализ заголовков...")
            titles = [v.title for v in videos]
            title_analysis = self.groq.analyze_titles(titles)
            
            self._report_progress("analyze", 80, "AI анализ стиля...")
            descriptions = [v.description for v in videos]
            style_analysis = self.groq.analyze_style(descriptions, titles)
            
            self._report_progress("analyze", 90, "Создание профиля...")
            profile = self.profile_manager.create_profile_from_analysis(
                channel_info.to_dict(),
                stats,
                title_analysis,
                style_analysis,
                niche
            )
            
            filepath = self.profile_manager.save_profile(profile)
            
            self.project_data['profile'] = profile
            self.project_data['competitor_tags'] = [tag for tag, _ in stats.get('top_tags', [])]
            
            self._report_progress("analyze", 100, "Анализ завершён!")
            
            return PipelineResult(True, "analyze", {
                'profile': profile,
                'stats': stats,
                'filepath': str(filepath)
            })
            
        except Exception as e:
            return PipelineResult(False, "analyze", {}, str(e))
    
    def generate_ideas(self, topic: str, count: int = 5) -> PipelineResult:
        """Этап 2: Генерация идей"""
        try:
            profile = self.project_data.get('profile')
            style_info = profile.get_style_summary() if profile else ""
            
            self._report_progress("ideas", 30, "Генерация подниши...")
            subniche = self.groq.generate_subniche(topic, style_info)
            
            self._report_progress("ideas", 70, "Генерация тем...")
            topics = self.groq.generate_video_topics(
                subniche.get('recommended', topic),
                style_info,
                count
            )
            
            self.project_data['subniche'] = subniche
            self.project_data['topics'] = topics
            
            self._report_progress("ideas", 100, "Идеи готовы!")
            
            return PipelineResult(True, "ideas", {
                'subniche': subniche,
                'topics': topics
            })
            
        except Exception as e:
            return PipelineResult(False, "ideas", {}, str(e))
    
    def generate_script(self, title: str, duration: str, style: str) -> PipelineResult:
        """Этап 3: Генерация сценария"""
        try:
            self._report_progress("script", 20, "Генерация сценария...")
            
            script = self.groq.generate_script(title, duration, style)
            
            self._report_progress("script", 80, "Анализ структуры...")
            scenes = self.script_parser.parse(script)
            duration_info = self.script_parser.get_total_duration(scenes)
            
            self.project_data['title'] = title
            self.project_data['script'] = script
            self.project_data['scenes'] = scenes
            self.project_data['duration_info'] = duration_info
            
            self._report_progress("script", 100, "Сценарий готов!")
            
            return PipelineResult(True, "script", {
                'script': script,
                'scenes': scenes,
                'duration': duration_info
            })
            
        except Exception as e:
            return PipelineResult(False, "script", {}, str(e))
    
    def generate_prompts(self) -> PipelineResult:
        """Этап 4: Генерация промптов для изображений"""
        try:
            script = self.project_data.get('script', '')
            title = self.project_data.get('title', '')
            profile = self.project_data.get('profile')
            style_info = profile.get_style_summary() if profile else ""
            
            self._report_progress("prompts", 30, "Генерация промптов для превью...")
            preview_prompts = self.groq.generate_preview_prompts(title, style_info)
            
            self._report_progress("prompts", 70, "Генерация промптов для сцен...")
            image_prompts = self.groq.generate_image_prompts(script, "Cinematic")
            
            self.project_data['preview_prompts'] = preview_prompts
            self.project_data['image_prompts'] = image_prompts
            
            self._report_progress("prompts", 100, "Промпты готовы!")
            
            return PipelineResult(True, "prompts", {
                'preview_prompts': preview_prompts,
                'image_prompts': image_prompts
            })
            
        except Exception as e:
            return PipelineResult(False, "prompts", {}, str(e))
    
    def generate_voice(self, voice_id: str) -> PipelineResult:
        """Этап 5: Озвучка"""
        try:
            script = self.project_data.get('script', '')
            title = self.project_data.get('title', 'video')
            
            # Папка для аудио
            audio_dir = self.output_dir / "audio"
            audio_dir.mkdir(exist_ok=True)
            
            self._report_progress("voice", 20, "Генерация озвучки...")
            
            audio_files = self.elevenlabs.generate_full_voiceover(
                script,
                voice_id,
                audio_dir
            )
            
            self.project_data['audio_files'] = [str(f) for f in audio_files]
            self.project_data['voice_id'] = voice_id
            
            self._report_progress("voice", 100, "Озвучка готова!")
            
            return PipelineResult(True, "voice", {
                'audio_files': [str(f) for f in audio_files]
            })
            
        except Exception as e:
            return PipelineResult(False, "voice", {}, str(e))
    
    def generate_seo(self) -> PipelineResult:
        """Этап 6: SEO оптимизация"""
        try:
            title = self.project_data.get('title', '')
            script = self.project_data.get('script', '')
            competitor_tags = self.project_data.get('competitor_tags', [])
            
            self._report_progress("seo", 50, "Генерация SEO...")
            
            seo_data = self.groq.generate_seo(title, script, competitor_tags)
            
            self.project_data['seo'] = seo_data
            
            self._report_progress("seo", 100, "SEO готов!")
            
            return PipelineResult(True, "seo", seo_data)
            
        except Exception as e:
            return PipelineResult(False, "seo", {}, str(e))
    
    def render_video(self, images: List[Path], music_path: Optional[Path] = None) -> PipelineResult:
        """Этап 7: Рендер видео"""
        try:
            audio_files = self.project_data.get('audio_files', [])
            title = self.project_data.get('title', 'video')
            
            if not audio_files:
                return PipelineResult(False, "render", {}, "Нет аудио файлов")
            
            if not images:
                return PipelineResult(False, "render", {}, "Нет изображений")
            
            self._report_progress("render", 20, "Подготовка к рендеру...")
            
            editor = VideoEditor(VideoConfig())
            
            output_path = self.output_dir / f"{title}.mp4"
            
            self._report_progress("render", 50, "Рендер видео...")
            
            editor.create_video_simple(
                images,
                Path(audio_files[0]),
                output_path,
                music_path,
                0.15
            )
            
            self.project_data['output_video'] = str(output_path)
            
            # Генерируем субтитры
            self._report_progress("render", 90, "Генерация субтитров...")
            srt_gen = SRTGenerator()
            srt_path = output_path.with_suffix('.srt')
            srt_gen.generate_from_script(self.project_data.get('script', ''), srt_path)
            self.project_data['output_srt'] = str(srt_path)
            
            self._report_progress("render", 100, "Видео готово!")
            
            return PipelineResult(True, "render", {
                'video_path': str(output_path),
                'srt_path': str(srt_path)
            })
            
        except Exception as e:
            return PipelineResult(False, "render", {}, str(e))
    
    def export_project(self) -> PipelineResult:
        """Этап 8: Экспорт проекта"""
        try:
            title = self.project_data.get('title', 'video')
            
            self._report_progress("export", 50, "Экспорт проекта...")
            
            exporter = ProjectExporter(self.output_dir)
            
            result = exporter.export_project(
                project_name=title,
                video_path=Path(self.project_data.get('output_video', '')) if self.project_data.get('output_video') else None,
                srt_path=Path(self.project_data.get('output_srt', '')) if self.project_data.get('output_srt') else None,
                script_text=self.project_data.get('script', ''),
                seo_data=self.project_data.get('seo'),
                image_prompts=[p.get('prompt_en', '') for p in self.project_data.get('image_prompts', [])],
                preview_prompts=[p.get('prompt_en', '') for p in self.project_data.get('preview_prompts', [])]
            )
            
            self._report_progress("export", 100, "Экспорт завершён!")
            
            return PipelineResult(result.success, "export", {
                'export_path': str(result.export_path),
                'files': result.files
            }, result.message if not result.success else "")
            
        except Exception as e:
            return PipelineResult(False, "export", {}, str(e))
    
    def save_project(self, filepath: Path):
        """Сохранение проекта"""
        # Конвертируем объекты в словари
        data = {}
        for key, value in self.project_data.items():
            if hasattr(value, 'to_dict'):
                data[key] = value.to_dict()
            elif hasattr(value, '__dict__'):
                data[key] = value.__dict__
            else:
                data[key] = value
        
        data['saved_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def load_project(self, filepath: Path):
        """Загрузка проекта"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.project_data = json.load(f)
