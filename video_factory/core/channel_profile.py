"""
Профиль канала — сохранение стиля для повторного использования
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field


@dataclass
class ChannelProfile:
    """Профиль анализированного канала"""
    
    # Основная информация
    name: str
    channel_id: str
    channel_url: str
    niche: str
    
    # Статистика
    subscribers: int = 0
    total_views: int = 0
    video_count: int = 0
    avg_views: int = 0
    avg_likes: int = 0
    engagement_rate: float = 0.0
    
    # Триггеры заголовков
    title_triggers: Dict[str, List[str]] = field(default_factory=dict)
    title_patterns: List[str] = field(default_factory=list)
    effective_words: List[str] = field(default_factory=list)
    
    # Стиль контента
    narrative_style: str = ""
    tone: str = ""
    target_audience: str = ""
    content_structure: str = ""
    unique_features: List[str] = field(default_factory=list)
    
    # Рекомендации по голосу
    voice_gender: str = ""
    voice_type: str = ""
    voice_pace: str = ""
    voice_emotion: str = ""
    
    # SEO
    top_tags: List[str] = field(default_factory=list)
    
    # Мета
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChannelProfile":
        return cls(**data)
    
    def get_style_summary(self) -> str:
        """Краткое описание стиля для промптов"""
        return f"""
Стиль: {self.narrative_style}
Тон: {self.tone}
Аудитория: {self.target_audience}
Особенности: {', '.join(self.unique_features)}
Структура: {self.content_structure}
Голос: {self.voice_gender}, {self.voice_type}, темп {self.voice_pace}
"""
    
    def get_triggers_summary(self) -> str:
        """Сводка по триггерам"""
        lines = ["ТРИГГЕРЫ ЗАГОЛОВКОВ:"]
        for category, triggers in self.title_triggers.items():
            if triggers:
                lines.append(f"• {category}: {', '.join(triggers[:5])}")
        
        if self.title_patterns:
            lines.append(f"\nПАТТЕРНЫ: {', '.join(self.title_patterns[:5])}")
        
        if self.effective_words:
            lines.append(f"\nЭФФЕКТИВНЫЕ СЛОВА: {', '.join(self.effective_words[:10])}")
        
        return '\n'.join(lines)


class ProfileManager:
    """Менеджер профилей каналов"""
    
    def __init__(self, profiles_dir: Path):
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def save_profile(self, profile: ChannelProfile) -> Path:
        """Сохранение профиля"""
        profile.updated_at = datetime.now().isoformat()
        
        # Безопасное имя файла
        safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in profile.name)
        filename = f"{safe_name}_{profile.channel_id[:8]}.json"
        filepath = self.profiles_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_profile(self, filepath: Path) -> Optional[ChannelProfile]:
        """Загрузка профиля"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ChannelProfile.from_dict(data)
        except Exception as e:
            print(f"Ошибка загрузки профиля: {e}")
            return None
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """Список всех профилей"""
        profiles = []
        
        for filepath in self.profiles_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                profiles.append({
                    'filepath': str(filepath),
                    'name': data.get('name', 'Unknown'),
                    'niche': data.get('niche', ''),
                    'subscribers': data.get('subscribers', 0),
                    'updated_at': data.get('updated_at', '')
                })
            except:
                continue
        
        return sorted(profiles, key=lambda x: x['updated_at'], reverse=True)
    
    def delete_profile(self, filepath: Path) -> bool:
        """Удаление профиля"""
        try:
            filepath.unlink()
            return True
        except:
            return False
    
    def create_profile_from_analysis(
        self,
        channel_info: Dict,
        stats: Dict,
        title_analysis: Dict,
        style_analysis: Dict,
        niche: str
    ) -> ChannelProfile:
        """Создание профиля из результатов анализа"""
        
        # Извлекаем данные о голосе
        voice = style_analysis.get('recommended_voice', {})
        
        profile = ChannelProfile(
            name=channel_info.get('title', 'Unknown'),
            channel_id=channel_info.get('channel_id', ''),
            channel_url=channel_info.get('custom_url', ''),
            niche=niche,
            
            # Статистика
            subscribers=channel_info.get('subscriber_count', 0),
            total_views=channel_info.get('view_count', 0),
            video_count=channel_info.get('video_count', 0),
            avg_views=stats.get('avg_views', 0),
            avg_likes=stats.get('avg_likes', 0),
            engagement_rate=stats.get('engagement_rate', 0),
            
            # Триггеры
            title_triggers=title_analysis.get('triggers', {}),
            title_patterns=title_analysis.get('patterns', []),
            effective_words=title_analysis.get('effective_words', []),
            
            # Стиль
            narrative_style=style_analysis.get('narrative_style', ''),
            tone=style_analysis.get('tone', ''),
            target_audience=style_analysis.get('target_audience', ''),
            content_structure=style_analysis.get('content_structure', ''),
            unique_features=style_analysis.get('unique_features', []),
            
            # Голос
            voice_gender=voice.get('gender', ''),
            voice_type=voice.get('type', ''),
            voice_pace=voice.get('pace', ''),
            voice_emotion=voice.get('emotion', ''),
            
            # SEO
            top_tags=[tag for tag, _ in stats.get('top_tags', [])]
        )
        
        return profile
