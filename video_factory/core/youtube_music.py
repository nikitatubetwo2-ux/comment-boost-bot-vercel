"""
Работа с YouTube Audio Library
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class AudioTrack:
    """Трек из Audio Library"""
    title: str
    artist: str
    genre: str
    mood: str
    duration: str
    url: str = ""
    downloaded: bool = False
    local_path: str = ""


class YouTubeAudioLibrary:
    """Помощник для работы с YouTube Audio Library"""
    
    # Категории музыки
    GENRES = [
        "Ambient",
        "Cinematic", 
        "Classical",
        "Country & Folk",
        "Dance & Electronic",
        "Hip Hop & Rap",
        "Jazz & Blues",
        "Pop",
        "R&B & Soul",
        "Rock"
    ]
    
    MOODS = [
        "Angry",
        "Bright",
        "Calm",
        "Dark",
        "Dramatic",
        "Funky",
        "Happy",
        "Inspirational",
        "Romantic",
        "Sad"
    ]
    
    # Рекомендации по жанрам для разных типов контента
    RECOMMENDATIONS = {
        "документальный": {
            "genres": ["Cinematic", "Ambient", "Classical"],
            "moods": ["Dramatic", "Dark", "Inspirational"]
        },
        "развлекательный": {
            "genres": ["Pop", "Dance & Electronic", "Hip Hop & Rap"],
            "moods": ["Bright", "Happy", "Funky"]
        },
        "образовательный": {
            "genres": ["Ambient", "Classical", "Jazz & Blues"],
            "moods": ["Calm", "Bright", "Inspirational"]
        },
        "драматический": {
            "genres": ["Cinematic", "Classical", "Rock"],
            "moods": ["Dramatic", "Dark", "Sad"]
        },
        "история": {
            "genres": ["Cinematic", "Classical", "Ambient"],
            "moods": ["Dramatic", "Dark", "Sad"]
        },
        "катастрофы": {
            "genres": ["Cinematic", "Ambient"],
            "moods": ["Dark", "Dramatic", "Sad"]
        },
        "тайны": {
            "genres": ["Ambient", "Cinematic"],
            "moods": ["Dark", "Dramatic", "Calm"]
        }
    }
    
    def __init__(self, music_dir: Path = None):
        self.music_dir = music_dir or Path.home() / "Music" / "YouTube Audio Library"
        self.music_dir.mkdir(parents=True, exist_ok=True)
    
    def get_recommendation(self, content_type: str, keywords: List[str] = None) -> Dict:
        """Получение рекомендации по музыке"""
        
        content_type = content_type.lower()
        
        # Ищем подходящую категорию
        rec = self.RECOMMENDATIONS.get(content_type)
        
        if not rec and keywords:
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in self.RECOMMENDATIONS:
                    rec = self.RECOMMENDATIONS[kw_lower]
                    break
        
        if not rec:
            rec = self.RECOMMENDATIONS["документальный"]
        
        return {
            "recommended_genres": rec["genres"],
            "recommended_moods": rec["moods"],
            "search_url": self._build_search_url(rec["genres"][0], rec["moods"][0]),
            "tips": [
                "Выбирайте треки без вокала для лучшего сочетания с озвучкой",
                "Громкость фоновой музыки: 10-20% от основного аудио",
                "Для драматических моментов используйте треки с нарастанием",
                "Все треки из YouTube Audio Library безопасны для монетизации"
            ]
        }
    
    def _build_search_url(self, genre: str, mood: str) -> str:
        """Построение URL для поиска в Audio Library"""
        base_url = "https://studio.youtube.com/channel/UC/music"
        # YouTube Studio использует свои параметры, но базовый URL работает
        return base_url
    
    def get_library_url(self) -> str:
        """URL YouTube Audio Library"""
        return "https://studio.youtube.com/channel/UC/music"
    
    def scan_local_music(self) -> List[AudioTrack]:
        """Сканирование локальной папки с музыкой"""
        tracks = []
        
        for ext in ["*.mp3", "*.wav", "*.m4a"]:
            for filepath in self.music_dir.glob(ext):
                tracks.append(AudioTrack(
                    title=filepath.stem,
                    artist="YouTube Audio Library",
                    genre="Unknown",
                    mood="Unknown",
                    duration="Unknown",
                    downloaded=True,
                    local_path=str(filepath)
                ))
        
        return tracks
    
    def get_track_for_scene(self, scene_mood: str) -> Dict:
        """Рекомендация трека для конкретной сцены"""
        
        mood_mapping = {
            "напряжённый": ["Dark", "Dramatic"],
            "грустный": ["Sad", "Calm"],
            "радостный": ["Happy", "Bright"],
            "загадочный": ["Dark", "Calm"],
            "эпичный": ["Dramatic", "Inspirational"],
            "спокойный": ["Calm", "Ambient"],
            "тревожный": ["Dark", "Dramatic"]
        }
        
        moods = mood_mapping.get(scene_mood.lower(), ["Calm"])
        
        return {
            "recommended_moods": moods,
            "search_tip": f"Ищите треки с настроением: {', '.join(moods)}"
        }


class SmartMusicSelector:
    """
    Умный подбор музыки — AI анализирует сценарий и подбирает музыку
    
    Анализирует:
    - Общее настроение сценария
    - Эмоциональные пики (драматичные моменты)
    - Темп повествования
    - Тематику контента
    """
    
    # Маппинг эмоций на музыкальные характеристики
    EMOTION_TO_MUSIC = {
        "напряжение": {"tempo": "medium-fast", "mood": "Dark", "genre": "Cinematic", "intensity": "high"},
        "драма": {"tempo": "slow-medium", "mood": "Dramatic", "genre": "Cinematic", "intensity": "high"},
        "грусть": {"tempo": "slow", "mood": "Sad", "genre": "Classical", "intensity": "low"},
        "радость": {"tempo": "fast", "mood": "Happy", "genre": "Pop", "intensity": "medium"},
        "тайна": {"tempo": "slow", "mood": "Dark", "genre": "Ambient", "intensity": "low"},
        "эпичность": {"tempo": "medium", "mood": "Inspirational", "genre": "Cinematic", "intensity": "high"},
        "спокойствие": {"tempo": "slow", "mood": "Calm", "genre": "Ambient", "intensity": "low"},
        "тревога": {"tempo": "medium-fast", "mood": "Dark", "genre": "Cinematic", "intensity": "medium"},
        "победа": {"tempo": "fast", "mood": "Bright", "genre": "Cinematic", "intensity": "high"},
        "поражение": {"tempo": "slow", "mood": "Sad", "genre": "Classical", "intensity": "medium"},
        "ужас": {"tempo": "variable", "mood": "Dark", "genre": "Ambient", "intensity": "high"},
        "надежда": {"tempo": "medium", "mood": "Inspirational", "genre": "Cinematic", "intensity": "medium"},
    }
    
    # Ключевые слова для определения эмоций
    EMOTION_KEYWORDS = {
        "напряжение": ["битва", "сражение", "атака", "оборона", "бой", "штурм", "осада"],
        "драма": ["трагедия", "гибель", "смерть", "потеря", "жертва", "катастрофа"],
        "грусть": ["печаль", "горе", "слёзы", "прощание", "утрата", "скорбь"],
        "тайна": ["загадка", "тайна", "секрет", "неизвестно", "мистерия", "скрытый"],
        "эпичность": ["великий", "легендарный", "исторический", "грандиозный", "масштабный"],
        "победа": ["победа", "триумф", "успех", "освобождение", "взятие"],
        "поражение": ["поражение", "разгром", "капитуляция", "отступление", "крах"],
        "ужас": ["ужас", "кошмар", "страх", "паника", "террор"],
        "надежда": ["надежда", "вера", "спасение", "возрождение", "новый"],
    }
    
    def __init__(self, music_dir: Path = None):
        self.music_dir = music_dir or Path("video_factory/data/music")
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.library = YouTubeAudioLibrary(self.music_dir)
    
    def analyze_script_mood(self, script: str) -> Dict:
        """
        AI анализ настроения сценария
        
        Returns:
            {
                "primary_mood": "драма",
                "secondary_moods": ["напряжение", "грусть"],
                "emotional_arc": [{"segment": 1, "mood": "тайна"}, ...],
                "recommended_music": {...}
            }
        """
        from core.groq_client import GroqClient
        from config import config
        
        if not config.api.groq_key:
            return self._fallback_analysis(script)
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        prompt = f"""Проанализируй эмоциональное настроение этого сценария для подбора фоновой музыки.

СЦЕНАРИЙ:
{script[:3000]}...

Определи:
1. Основное настроение (одно из: напряжение, драма, грусть, радость, тайна, эпичность, спокойствие, тревога, победа, поражение, ужас, надежда)
2. Дополнительные настроения
3. Эмоциональную арку (как меняется настроение по ходу сценария)
4. Рекомендации по музыке

Ответь в JSON:
{{
    "primary_mood": "драма",
    "secondary_moods": ["напряжение", "грусть"],
    "intensity": "high/medium/low",
    "tempo": "slow/medium/fast",
    "emotional_arc": [
        {{"segment": "Вступление", "mood": "тайна", "intensity": "low"}},
        {{"segment": "Развитие", "mood": "напряжение", "intensity": "medium"}},
        {{"segment": "Кульминация", "mood": "драма", "intensity": "high"}},
        {{"segment": "Финал", "mood": "грусть", "intensity": "medium"}}
    ],
    "music_keywords": ["epic", "orchestral", "dramatic"],
    "avoid_keywords": ["happy", "upbeat", "cheerful"]
}}"""

        response = groq._chat([
            {"role": "system", "content": "Ты музыкальный продюсер, специализирующийся на подборе музыки для документальных фильмов."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            import json
            json_match = response[response.find('{'):response.rfind('}')+1]
            analysis = json.loads(json_match)
            
            # Добавляем рекомендации по музыке
            primary = analysis.get('primary_mood', 'драма')
            music_params = self.EMOTION_TO_MUSIC.get(primary, self.EMOTION_TO_MUSIC['драма'])
            analysis['recommended_music'] = music_params
            
            return analysis
        except:
            return self._fallback_analysis(script)
    
    def _fallback_analysis(self, script: str) -> Dict:
        """Анализ без AI — по ключевым словам"""
        script_lower = script.lower()
        
        # Считаем совпадения ключевых слов
        emotion_scores = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in script_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Сортируем по количеству совпадений
        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_emotions[0][0] if sorted_emotions else "драма"
        secondary = [e[0] for e in sorted_emotions[1:3]] if len(sorted_emotions) > 1 else []
        
        music_params = self.EMOTION_TO_MUSIC.get(primary, self.EMOTION_TO_MUSIC['драма'])
        
        return {
            "primary_mood": primary,
            "secondary_moods": secondary,
            "intensity": music_params['intensity'],
            "tempo": music_params['tempo'],
            "recommended_music": music_params,
            "music_keywords": [music_params['mood'].lower(), music_params['genre'].lower()],
            "method": "keyword_fallback"
        }
    
    def find_matching_tracks(self, mood_analysis: Dict) -> List[AudioTrack]:
        """Поиск подходящих треков в локальной библиотеке"""
        
        local_tracks = self.library.scan_local_music()
        if not local_tracks:
            return []
        
        # Ключевые слова для поиска
        keywords = mood_analysis.get('music_keywords', [])
        mood = mood_analysis.get('recommended_music', {}).get('mood', 'Dramatic')
        genre = mood_analysis.get('recommended_music', {}).get('genre', 'Cinematic')
        
        search_terms = keywords + [mood.lower(), genre.lower()]
        
        # Ищем совпадения в названиях файлов
        matching = []
        for track in local_tracks:
            track_name = track.title.lower()
            score = sum(1 for term in search_terms if term in track_name)
            if score > 0:
                matching.append((track, score))
        
        # Сортируем по релевантности
        matching.sort(key=lambda x: x[1], reverse=True)
        
        return [t[0] for t in matching]
    
    def get_music_recommendation(self, script: str) -> Dict:
        """
        Полная рекомендация музыки для сценария
        
        Returns:
            {
                "analysis": {...},
                "local_matches": [...],
                "search_suggestions": [...],
                "youtube_library_url": "..."
            }
        """
        analysis = self.analyze_script_mood(script)
        local_matches = self.find_matching_tracks(analysis)
        
        # Формируем поисковые запросы для YouTube Audio Library
        music_params = analysis.get('recommended_music', {})
        search_suggestions = [
            f"{music_params.get('genre', 'Cinematic')} {music_params.get('mood', 'Dramatic')}",
            f"{analysis.get('primary_mood', 'драма')} music",
            f"epic {music_params.get('tempo', 'medium')} tempo"
        ]
        
        return {
            "analysis": analysis,
            "local_matches": [{"title": t.title, "path": t.local_path} for t in local_matches[:5]],
            "search_suggestions": search_suggestions,
            "youtube_library_url": self.library.get_library_url(),
            "tips": [
                f"Основное настроение: {analysis.get('primary_mood', 'драма')}",
                f"Рекомендуемый жанр: {music_params.get('genre', 'Cinematic')}",
                f"Темп: {music_params.get('tempo', 'medium')}",
                "Громкость фоновой музыки: 10-15% от голоса"
            ]
        }
