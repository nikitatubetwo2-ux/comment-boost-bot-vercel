"""
Проверка на copyright
"""

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class CopyrightStatus(Enum):
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    UNKNOWN = "unknown"


@dataclass
class CopyrightResult:
    """Результат проверки"""
    item: str
    item_type: str  # image, music, text
    status: CopyrightStatus
    message: str
    details: str = ""


class CopyrightChecker:
    """Проверка материалов на copyright"""
    
    # Безопасные источники музыки
    SAFE_MUSIC_SOURCES = [
        "youtube audio library",
        "youtube аудиобиблиотека",
        "pixabay",
        "mixkit",
        "bensound",
        "incompetech",
        "free music archive",
        "epidemic sound",  # если есть подписка
        "artlist",  # если есть подписка
    ]
    
    # Безопасные источники изображений
    SAFE_IMAGE_SOURCES = [
        "ai generated",
        "whisk",
        "midjourney",
        "dall-e",
        "stable diffusion",
        "unsplash",
        "pexels",
        "pixabay",
        "собственное фото",
        "own photo",
    ]
    
    def __init__(self):
        self.results: List[CopyrightResult] = []
    
    def check_music(self, music_info: Dict[str, Any]) -> CopyrightResult:
        """Проверка музыки"""
        source = music_info.get('source', '').lower()
        title = music_info.get('title', 'Unknown')
        
        # Проверяем источник
        is_safe = any(safe in source for safe in self.SAFE_MUSIC_SOURCES)
        
        if is_safe:
            result = CopyrightResult(
                item=title,
                item_type="music",
                status=CopyrightStatus.SAFE,
                message="Музыка из безопасного источника",
                details=f"Источник: {source}"
            )
        elif "youtube" in source.lower():
            result = CopyrightResult(
                item=title,
                item_type="music",
                status=CopyrightStatus.SAFE,
                message="YouTube Audio Library — безопасно для монетизации",
                details="Бесплатная музыка от YouTube"
            )
        else:
            result = CopyrightResult(
                item=title,
                item_type="music",
                status=CopyrightStatus.WARNING,
                message="Проверьте лицензию музыки",
                details=f"Источник: {source}. Убедитесь в наличии лицензии."
            )
        
        self.results.append(result)
        return result
    
    def check_image(self, image_info: Dict[str, Any]) -> CopyrightResult:
        """Проверка изображения"""
        source = image_info.get('source', '').lower()
        path = image_info.get('path', 'Unknown')
        
        # AI-сгенерированные изображения безопасны
        is_ai = any(ai in source for ai in ['ai', 'whisk', 'midjourney', 'dall-e', 'stable diffusion', 'generated'])
        is_safe_source = any(safe in source for safe in self.SAFE_IMAGE_SOURCES)
        
        if is_ai or is_safe_source:
            result = CopyrightResult(
                item=str(path),
                item_type="image",
                status=CopyrightStatus.SAFE,
                message="Изображение безопасно",
                details=f"Источник: {source}"
            )
        else:
            result = CopyrightResult(
                item=str(path),
                item_type="image",
                status=CopyrightStatus.WARNING,
                message="Проверьте права на изображение",
                details="Убедитесь, что у вас есть права на использование"
            )
        
        self.results.append(result)
        return result
    
    def check_text(self, text_info: Dict[str, Any]) -> CopyrightResult:
        """Проверка текста"""
        source = text_info.get('source', '').lower()
        content_type = text_info.get('type', 'script')
        
        if 'original' in source or 'ai' in source or 'generated' in source:
            result = CopyrightResult(
                item=content_type,
                item_type="text",
                status=CopyrightStatus.SAFE,
                message="Оригинальный контент",
                details="Текст создан AI или является оригинальным"
            )
        elif 'quote' in source or 'цитата' in source:
            result = CopyrightResult(
                item=content_type,
                item_type="text",
                status=CopyrightStatus.WARNING,
                message="Содержит цитаты",
                details="Убедитесь, что цитаты используются в рамках fair use"
            )
        else:
            result = CopyrightResult(
                item=content_type,
                item_type="text",
                status=CopyrightStatus.SAFE,
                message="Текст проверен",
                details=""
            )
        
        self.results.append(result)
        return result
    
    def check_project(
        self,
        images: List[Dict],
        music: Dict,
        script_source: str = "ai_generated"
    ) -> Dict[str, Any]:
        """Полная проверка проекта"""
        
        self.results = []
        
        # Проверяем изображения
        for img in images:
            self.check_image(img)
        
        # Проверяем музыку
        self.check_music(music)
        
        # Проверяем текст
        self.check_text({'source': script_source, 'type': 'script'})
        
        # Подсчитываем статистику
        safe_count = sum(1 for r in self.results if r.status == CopyrightStatus.SAFE)
        warning_count = sum(1 for r in self.results if r.status == CopyrightStatus.WARNING)
        danger_count = sum(1 for r in self.results if r.status == CopyrightStatus.DANGER)
        
        # Определяем общий статус
        if danger_count > 0:
            overall_status = CopyrightStatus.DANGER
            overall_message = "⚠️ Обнаружены проблемы с авторскими правами!"
        elif warning_count > 0:
            overall_status = CopyrightStatus.WARNING
            overall_message = "⚡ Есть предупреждения, проверьте материалы"
        else:
            overall_status = CopyrightStatus.SAFE
            overall_message = "✅ Все материалы безопасны для монетизации"
        
        return {
            'overall_status': overall_status.value,
            'overall_message': overall_message,
            'safe_count': safe_count,
            'warning_count': warning_count,
            'danger_count': danger_count,
            'total_checked': len(self.results),
            'details': [
                {
                    'item': r.item,
                    'type': r.item_type,
                    'status': r.status.value,
                    'message': r.message,
                    'details': r.details
                }
                for r in self.results
            ]
        }
    
    def get_report(self) -> str:
        """Текстовый отчёт"""
        lines = ["=" * 50, "ОТЧЁТ О ПРОВЕРКЕ COPYRIGHT", "=" * 50, ""]
        
        for r in self.results:
            status_icon = {
                CopyrightStatus.SAFE: "✅",
                CopyrightStatus.WARNING: "⚠️",
                CopyrightStatus.DANGER: "❌",
                CopyrightStatus.UNKNOWN: "❓"
            }.get(r.status, "❓")
            
            lines.append(f"{status_icon} [{r.item_type.upper()}] {r.item}")
            lines.append(f"   {r.message}")
            if r.details:
                lines.append(f"   {r.details}")
            lines.append("")
        
        return '\n'.join(lines)
