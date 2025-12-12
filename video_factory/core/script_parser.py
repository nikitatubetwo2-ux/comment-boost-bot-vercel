"""
Парсер сценария — разбивка на сцены с таймкодами
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Scene:
    """Сцена из сценария"""
    index: int
    timecode_start: str
    timecode_end: str
    duration_seconds: float
    chapter_name: str
    text: str
    word_count: int
    needs_image: bool  # Нужно ли изображение для этой сцены


class ScriptParser:
    """Парсер сценария"""
    
    # Слов в минуту при озвучке
    WORDS_PER_MINUTE = 150
    
    # Паттерны для поиска глав
    CHAPTER_PATTERNS = [
        r'\[([^\]]+)\]',  # [INTRO - 0:00-0:30]
        r'\*\*([^*]+)\*\*',  # **Глава 1**
        r'^#{1,3}\s+(.+)$',  # # Заголовок
    ]
    
    def __init__(self, words_per_minute: int = 150):
        self.wpm = words_per_minute
    
    def parse(self, script: str) -> List[Scene]:
        """Разбор сценария на сцены"""
        
        scenes = []
        lines = script.split('\n')
        
        current_chapter = "INTRO"
        current_text = []
        current_timecode = "0:00"
        scene_index = 0
        total_seconds = 0
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Проверяем, это заголовок главы?
            chapter_match = None
            for pattern in self.CHAPTER_PATTERNS:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    chapter_match = match.group(1)
                    break
            
            if chapter_match:
                # Сохраняем предыдущую сцену
                if current_text:
                    text = '\n'.join(current_text)
                    word_count = len(text.split())
                    duration = (word_count / self.wpm) * 60
                    
                    scenes.append(Scene(
                        index=scene_index,
                        timecode_start=self._seconds_to_timecode(total_seconds),
                        timecode_end=self._seconds_to_timecode(total_seconds + duration),
                        duration_seconds=duration,
                        chapter_name=current_chapter,
                        text=text,
                        word_count=word_count,
                        needs_image=True
                    ))
                    
                    total_seconds += duration
                    scene_index += 1
                
                # Начинаем новую главу
                current_chapter = chapter_match
                current_text = []
                
                # Извлекаем таймкод если есть
                timecode_match = re.search(r'(\d{1,2}:\d{2})', chapter_match)
                if timecode_match:
                    current_timecode = timecode_match.group(1)
            else:
                # Обычный текст — добавляем к текущей сцене
                current_text.append(line)
        
        # Последняя сцена
        if current_text:
            text = '\n'.join(current_text)
            word_count = len(text.split())
            duration = (word_count / self.wpm) * 60
            
            scenes.append(Scene(
                index=scene_index,
                timecode_start=self._seconds_to_timecode(total_seconds),
                timecode_end=self._seconds_to_timecode(total_seconds + duration),
                duration_seconds=duration,
                chapter_name=current_chapter,
                text=text,
                word_count=word_count,
                needs_image=True
            ))
        
        return scenes
    
    def _seconds_to_timecode(self, seconds: float) -> str:
        """Конвертация секунд в таймкод MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def _timecode_to_seconds(self, timecode: str) -> float:
        """Конвертация таймкода в секунды"""
        parts = timecode.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    
    def get_image_schedule(
        self, 
        scenes: List[Scene],
        first_5min_interval: int = 30,  # секунд
        after_5min_interval: int = 40   # секунд
    ) -> List[Dict]:
        """
        Расписание изображений:
        - Первые 5 минут: каждые 30 секунд
        - После 5 минут: каждые 40 секунд
        """
        
        schedule = []
        image_index = 0
        
        for scene in scenes:
            start_sec = self._timecode_to_seconds(scene.timecode_start)
            end_sec = self._timecode_to_seconds(scene.timecode_end)
            
            current_sec = start_sec
            
            while current_sec < end_sec:
                # Определяем интервал
                if current_sec < 300:  # 5 минут
                    interval = first_5min_interval
                else:
                    interval = after_5min_interval
                
                schedule.append({
                    'index': image_index,
                    'timecode': self._seconds_to_timecode(current_sec),
                    'seconds': current_sec,
                    'scene_index': scene.index,
                    'chapter': scene.chapter_name,
                    'context': scene.text[:200]  # Контекст для промпта
                })
                
                image_index += 1
                current_sec += interval
        
        return schedule
    
    def get_total_duration(self, scenes: List[Scene]) -> Dict:
        """Общая длительность"""
        total_seconds = sum(s.duration_seconds for s in scenes)
        total_words = sum(s.word_count for s in scenes)
        
        return {
            'total_seconds': total_seconds,
            'total_minutes': total_seconds / 60,
            'formatted': self._seconds_to_timecode(total_seconds),
            'total_words': total_words,
            'scenes_count': len(scenes)
        }
    
    def estimate_costs(self, scenes: List[Scene]) -> Dict:
        """Оценка затрат на озвучку"""
        total_chars = sum(len(s.text) for s in scenes)
        
        # ElevenLabs тарифы (примерно)
        costs = {
            'total_characters': total_chars,
            'elevenlabs_starter': f"${total_chars / 30000 * 5:.2f}",  # $5 за 30K
            'elevenlabs_creator': f"${total_chars / 100000 * 22:.2f}",  # $22 за 100K
            'elevenlabs_pro': f"${total_chars / 500000 * 99:.2f}",  # $99 за 500K
        }
        
        return costs
