"""
Система профилей каналов — запоминание стиля для каждого канала
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field


@dataclass
class ChannelStyle:
    """
    Профиль стиля канала — запоминает ВСЕ настройки для канала
    
    Один раз настроил → все будущие видео в этом стиле
    """
    
    # Идентификация
    id: str                              # Уникальный ID профиля
    name: str                            # Название канала/профиля
    created_at: str = ""
    updated_at: str = ""
    
    # Источник копирования
    competitor_channel: str = ""          # Канал-конкурент для копирования
    competitor_name: str = ""             # Название конкурента
    
    # Выбранная подниша
    main_niche: str = ""                  # Основная ниша (военная история)
    sub_niche: str = ""                   # Подниша (малоизвестные битвы WW2)
    sub_niche_description: str = ""       # Описание подниши
    rejected_subniches: List[str] = field(default_factory=list)  # Отклонённые подниши
    
    # Стиль контента (ЗАПОМИНАЕТСЯ)
    narrative_style: str = ""             # Стиль повествования
    tone: str = ""                        # Тон (драматичный, спокойный)
    target_audience: str = ""             # Целевая аудитория
    
    # Голос (ЗАПОМИНАЕТСЯ)
    voice_id: str = ""                    # ID голоса ElevenLabs
    voice_name: str = ""                  # Название голоса
    voice_stability: float = 0.5
    voice_clarity: float = 0.75
    
    # Визуальный стиль (ЗАПОМИНАЕТСЯ)
    image_style: str = ""                 # Стиль изображений
    color_correction: str = ""            # Цветокоррекция
    
    # Эффекты и переходы (ЗАПОМИНАЕТСЯ)
    transitions: List[str] = field(default_factory=list)
    zoom_effect: float = 1.05
    pan_effect: bool = True
    
    # Музыка (ЗАПОМИНАЕТСЯ)
    music_mood: str = ""                  # Настроение музыки
    music_genre: str = ""                 # Жанр
    
    # Тайминги изображений
    intro_image_interval: int = 10        # Интервал первые 5 мин (сек)
    main_image_interval: int = 40         # Интервал после 5 мин (сек)
    
    # Сгенерированные темы для этого канала
    generated_topics: List[Dict] = field(default_factory=list)
    approved_topics: List[str] = field(default_factory=list)  # Одобренные темы
    
    # Статистика
    videos_created: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChannelStyle':
        # Обработка списков
        for key in ['rejected_subniches', 'transitions', 'generated_topics', 'approved_topics']:
            if key not in data:
                data[key] = []
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ChannelStyleManager:
    """
    Менеджер профилей каналов
    
    Возможности:
    - Создание профиля на основе анализа конкурента
    - Запоминание всех настроек
    - Генерация тем в рамках выбранной подниши
    - Применение стиля к новым проектам
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("video_factory/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.styles_file = self.data_dir / "channel_styles.json"
        self.styles: Dict[str, ChannelStyle] = {}
        self._load()
    
    def _load(self):
        """Загрузка профилей"""
        if self.styles_file.exists():
            try:
                data = json.loads(self.styles_file.read_text())
                for sid, sdata in data.items():
                    self.styles[sid] = ChannelStyle.from_dict(sdata)
            except Exception as e:
                print(f"Ошибка загрузки профилей: {e}")
    
    def _save(self):
        """Сохранение профилей"""
        data = {sid: s.to_dict() for sid, s in self.styles.items()}
        self.styles_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def create_style(self, name: str, competitor_channel: str = "") -> ChannelStyle:
        """Создание нового профиля канала"""
        import time
        style_id = f"style_{int(time.time())}_{len(self.styles)}"
        
        style = ChannelStyle(
            id=style_id,
            name=name,
            created_at=datetime.now().isoformat(),
            competitor_channel=competitor_channel
        )
        
        self.styles[style_id] = style
        self._save()
        return style
    
    def get_style(self, style_id: str) -> Optional[ChannelStyle]:
        return self.styles.get(style_id)
    
    def get_all_styles(self) -> List[ChannelStyle]:
        return list(self.styles.values())
    
    def update_style(self, style_id: str, **kwargs):
        """Обновление профиля"""
        if style_id in self.styles:
            style = self.styles[style_id]
            for key, value in kwargs.items():
                if hasattr(style, key):
                    setattr(style, key, value)
            style.updated_at = datetime.now().isoformat()
            self._save()
    
    def delete_style(self, style_id: str):
        """Удаление профиля"""
        if style_id in self.styles:
            del self.styles[style_id]
            self._save()
    
    def analyze_and_setup(self, style_id: str) -> Dict[str, Any]:
        """
        Полный анализ конкурента и настройка профиля
        
        1. Анализ канала конкурента
        2. Определение стиля
        3. Поиск подниш с низкой конкуренцией
        4. Настройка всех параметров
        """
        style = self.styles.get(style_id)
        if not style or not style.competitor_channel:
            return {"error": "Профиль не найден или не указан конкурент"}
        
        from .youtube_analyzer import YouTubeAnalyzer
        from .groq_client import GroqClient
        from config import config
        
        result = {"status": "ok", "steps": []}
        
        try:
            # 1. Получаем данные канала
            analyzer = YouTubeAnalyzer(config.api.youtube_keys)
            channel_info = analyzer.get_channel_info(style.competitor_channel)
            
            if not channel_info:
                return {"error": "Канал не найден"}
            
            style.competitor_name = channel_info.title
            result["steps"].append(f"✅ Канал найден: {channel_info.title}")
            
            # 2. Получаем видео
            videos = analyzer.get_channel_videos(channel_info.channel_id, max_results=15)
            titles = [v.title for v in videos]
            descriptions = [v.description for v in videos if v.description]
            
            # 3. AI анализ стиля
            groq = GroqClient(config.api.groq_key, config.api.groq_model)
            
            style_analysis = groq.analyze_style(descriptions, titles)
            result["steps"].append("✅ Стиль проанализирован")
            
            # Применяем стиль
            style.narrative_style = style_analysis.get('narrative_style', 'Документальный')
            style.tone = style_analysis.get('tone', 'Драматичный')
            style.target_audience = style_analysis.get('target_audience', 'Широкая аудитория')
            
            # Голос
            voice_rec = style_analysis.get('recommended_voice', {})
            style.voice_name, style.voice_id = self._select_voice(voice_rec)
            
            # Визуальный стиль
            style.image_style = self._determine_image_style(titles, style_analysis)
            style.color_correction = "cinematic"
            
            # Эффекты
            style.transitions = ["fade", "dissolve", "crossfade"]
            style.zoom_effect = 1.05
            style.pan_effect = True
            
            # Музыка
            style.music_mood = self._determine_music(titles)
            
            result["steps"].append("✅ Параметры настроены")
            
            # 4. Определяем нишу
            style.main_niche = self._extract_niche(titles)
            
            # 5. Ищем подниши
            channels_info = f"Канал: {channel_info.title}\nПодписчики: {channel_info.subscriber_count}\nВидео: {', '.join(titles[:10])}"
            niche_analysis = groq.analyze_niche(style.main_niche, channels_info)
            
            result["niche_analysis"] = niche_analysis
            result["steps"].append("✅ Подниши найдены")
            
            # Сохраняем
            style.updated_at = datetime.now().isoformat()
            self._save()
            
            result["style"] = style.to_dict()
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def select_subniche(self, style_id: str, subniche_name: str, subniche_description: str):
        """Выбор подниши для канала"""
        if style_id in self.styles:
            style = self.styles[style_id]
            style.sub_niche = subniche_name
            style.sub_niche_description = subniche_description
            style.updated_at = datetime.now().isoformat()
            self._save()
    
    def reject_subniche(self, style_id: str, subniche_name: str):
        """Отклонение подниши (чтобы не предлагалась снова)"""
        if style_id in self.styles:
            style = self.styles[style_id]
            if subniche_name not in style.rejected_subniches:
                style.rejected_subniches.append(subniche_name)
            self._save()
    
    def generate_topics(self, style_id: str, count: int = 5) -> List[Dict]:
        """
        Генерация тем для канала В РАМКАХ выбранной подниши
        
        Темы генерируются только по выбранной подниши,
        не предлагаются совсем другие направления
        """
        style = self.styles.get(style_id)
        if not style:
            return []
        
        from .groq_client import GroqClient
        from config import config
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        # Формируем контекст
        context = f"""
КАНАЛ: {style.name}
ОСНОВНАЯ НИША: {style.main_niche}
ВЫБРАННАЯ ПОДНИША: {style.sub_niche}
ОПИСАНИЕ ПОДНИШИ: {style.sub_niche_description}
СТИЛЬ: {style.narrative_style}, {style.tone}
ЦЕЛЕВАЯ АУДИТОРИЯ: {style.target_audience}

УЖЕ ОДОБРЕННЫЕ ТЕМЫ (не повторять):
{chr(10).join(style.approved_topics[-20:])}
"""
        
        topics = groq.generate_video_topics(
            subniche=f"{style.sub_niche}: {style.sub_niche_description}",
            style_info=context,
            count=count
        )
        
        # Сохраняем сгенерированные темы
        style.generated_topics.extend(topics)
        self._save()
        
        return topics
    
    def approve_topic(self, style_id: str, topic_title: str):
        """Одобрение темы (добавляется в список для избежания повторов)"""
        if style_id in self.styles:
            style = self.styles[style_id]
            if topic_title not in style.approved_topics:
                style.approved_topics.append(topic_title)
            self._save()
    
    def apply_style_to_project(self, style_id: str, project: Any) -> Any:
        """
        Применение стиля канала к проекту
        
        Все настройки из профиля переносятся в проект
        """
        style = self.styles.get(style_id)
        if not style:
            return project
        
        # Применяем все сохранённые настройки
        project.ai_style = style.narrative_style
        project.ai_voice = style.voice_name
        project.ai_image_style = style.image_style
        project.ai_transitions = style.transitions.copy()
        project.ai_effects = {
            "zoom": style.zoom_effect,
            "pan": style.pan_effect,
            "color_correction": style.color_correction
        }
        project.ai_music_mood = style.music_mood
        
        return project
    
    def increment_videos(self, style_id: str):
        """Увеличение счётчика созданных видео"""
        if style_id in self.styles:
            self.styles[style_id].videos_created += 1
            self._save()
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _select_voice(self, voice_rec: dict) -> tuple:
        """
        УМНЫЙ выбор голоса на основе полного анализа конкурента
        
        Учитывает:
        - gender (male/female)
        - age (young/middle/old)
        - tone (serious/casual/dramatic)
        - speed (slow/medium/fast)
        - emotion (calm/energetic/dramatic)
        """
        from .voice_library import VOICE_LIBRARY, get_voices_by_category
        
        gender = voice_rec.get('gender', 'male').lower()
        age = voice_rec.get('age', 'middle').lower()
        tone = voice_rec.get('tone', 'serious').lower()
        emotion = voice_rec.get('emotion', 'calm').lower()
        
        # Нормализуем gender
        if 'female' in gender or 'женск' in gender:
            gender = 'female'
        else:
            gender = 'male'
        
        # === МАТРИЦА ВЫБОРА ГОЛОСА ===
        # Приоритет: tone + emotion → age → gender
        
        best_voice = None
        best_score = 0
        
        for voice_id, voice in VOICE_LIBRARY.items():
            if voice.gender != gender:
                continue
            
            score = 0
            
            # Возраст (20 баллов)
            if voice.age == age:
                score += 20
            elif (age == 'middle' and voice.age in ['young', 'old']):
                score += 10  # middle совместим с любым
            
            # Тон и эмоция (40 баллов)
            if tone == 'serious' or tone == 'dramatic':
                if voice.category == 'narration':
                    score += 30
                if 'documentary' in voice.use_case or 'military' in voice.use_case:
                    score += 10
            elif tone == 'casual':
                if voice.category == 'conversational':
                    score += 30
                if 'podcast' in voice.use_case or 'vlog' in voice.use_case:
                    score += 10
            
            # Эмоциональность (20 баллов)
            if emotion == 'dramatic':
                if 'drama' in voice.use_case or 'intense' in voice.use_case:
                    score += 20
                elif voice.category == 'narration':
                    score += 10
            elif emotion == 'calm':
                if 'calm' in voice.use_case or 'meditation' in voice.use_case:
                    score += 20
                elif 'audiobook' in voice.use_case:
                    score += 10
            elif emotion == 'energetic':
                if 'energetic' in voice.use_case or 'gaming' in voice.use_case:
                    score += 20
            
            # Бонус за военную тематику (для нашего проекта)
            if 'military' in voice.use_case or 'history' in voice.use_case:
                score += 15
            
            if score > best_score:
                best_score = score
                best_voice = voice
        
        if best_voice:
            display_name = f"{best_voice.name} ({best_voice.gender}, {best_voice.accent})"
            return (display_name, best_voice.voice_id)
        
        # Fallback — Brian для мужского, Rachel для женского
        if gender == 'female':
            return ("Rachel (female, american)", "21m00Tcm4TlvDq8ikWAM")
        return ("Brian (male, american)", "nPczCjzI2devNBz1zQrb")
    
    def _determine_image_style(self, titles: List[str], style: dict) -> str:
        """Определение стиля изображений"""
        titles_text = " ".join(titles).lower()
        
        if any(w in titles_text for w in ['война', 'военн', 'ww2', 'битва', 'сражен', 'war', 'battle']):
            return "war photography, dramatic, gritty, cinematic, 8k, hyperrealistic, historical accuracy"
        elif any(w in titles_text for w in ['истори', 'древн', 'средневеков', 'history', 'ancient']):
            return "historical documentary, cinematic lighting, detailed, 8k, photorealistic"
        elif any(w in titles_text for w in ['космос', 'планет', 'галакти', 'space']):
            return "space, sci-fi, epic, cinematic, 8k, detailed, cosmic"
        elif any(w in titles_text for w in ['тайн', 'загадк', 'мистер', 'mystery']):
            return "mysterious, dark, atmospheric, cinematic, 8k, moody lighting"
        else:
            return "cinematic, dramatic lighting, 8k, hyperrealistic, detailed"
    
    def _determine_music(self, titles: List[str]) -> str:
        """Определение настроения музыки"""
        titles_text = " ".join(titles).lower()
        
        if any(w in titles_text for w in ['война', 'битва', 'сражен']):
            return "epic, dramatic, orchestral, intense"
        elif any(w in titles_text for w in ['тайн', 'загадк', 'мистер']):
            return "mysterious, suspenseful, ambient, dark"
        elif any(w in titles_text for w in ['ужас', 'страш']):
            return "horror, tense, dark ambient"
        else:
            return "cinematic, emotional, orchestral"
    
    def _extract_niche(self, titles: List[str]) -> str:
        """Извлечение основной ниши из заголовков"""
        titles_text = " ".join(titles).lower()
        
        if any(w in titles_text for w in ['война', 'ww2', 'ww1', 'битва']):
            return "Военная история"
        elif any(w in titles_text for w in ['истори', 'древн']):
            return "История"
        elif any(w in titles_text for w in ['космос', 'планет']):
            return "Космос и наука"
        elif any(w in titles_text for w in ['тайн', 'загадк']):
            return "Тайны и загадки"
        else:
            return "Документальный контент"
