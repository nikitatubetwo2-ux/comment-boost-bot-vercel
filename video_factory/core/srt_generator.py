"""
Генератор SRT субтитров
"""

import re
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Subtitle:
    """Один субтитр"""
    index: int
    start_time: str  # формат: 00:00:00,000
    end_time: str
    text: str
    
    def to_srt(self) -> str:
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{self.text}\n"


class SRTGenerator:
    """Генератор SRT файлов"""
    
    def __init__(self, words_per_minute: int = 150):
        self.wpm = words_per_minute
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Конвертация секунд в формат SRT (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _srt_time_to_seconds(self, srt_time: str) -> float:
        """Конвертация SRT времени в секунды"""
        parts = srt_time.replace(',', ':').split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        millis = int(parts[3]) if len(parts) > 3 else 0
        return hours * 3600 + minutes * 60 + seconds + millis / 1000
    
    def _split_into_chunks(self, text: str, max_chars: int = 80) -> List[str]:
        """Разбивка текста на строки для субтитров"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_chars:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def generate_from_script(
        self,
        script: str,
        output_path: Path,
        max_chars_per_line: int = 42,
        max_lines: int = 2,
        min_duration: float = 1.0,
        max_duration: float = 5.0
    ) -> Path:
        """Генерация SRT из сценария"""
        
        # Убираем таймкоды и заголовки глав
        clean_script = re.sub(r'\[.*?\]', '', script)
        clean_script = re.sub(r'---+', '', clean_script)
        clean_script = clean_script.strip()
        
        # Разбиваем на предложения
        sentences = re.split(r'(?<=[.!?])\s+', clean_script)
        
        subtitles = []
        current_time = 0.0
        index = 1
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Рассчитываем длительность на основе количества слов
            word_count = len(sentence.split())
            duration = (word_count / self.wpm) * 60
            duration = max(min_duration, min(duration, max_duration))
            
            # Разбиваем длинные предложения
            if len(sentence) > max_chars_per_line * max_lines:
                chunks = self._split_into_chunks(sentence, max_chars_per_line * max_lines)
                chunk_duration = duration / len(chunks)
                
                for chunk in chunks:
                    # Форматируем в 2 строки если нужно
                    lines = self._split_into_chunks(chunk, max_chars_per_line)
                    text = '\n'.join(lines[:max_lines])
                    
                    subtitles.append(Subtitle(
                        index=index,
                        start_time=self._seconds_to_srt_time(current_time),
                        end_time=self._seconds_to_srt_time(current_time + chunk_duration),
                        text=text
                    ))
                    
                    current_time += chunk_duration
                    index += 1
            else:
                # Форматируем в 2 строки если нужно
                lines = self._split_into_chunks(sentence, max_chars_per_line)
                text = '\n'.join(lines[:max_lines])
                
                subtitles.append(Subtitle(
                    index=index,
                    start_time=self._seconds_to_srt_time(current_time),
                    end_time=self._seconds_to_srt_time(current_time + duration),
                    text=text
                ))
                
                current_time += duration
                index += 1
        
        # Записываем SRT файл
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sub in subtitles:
                f.write(sub.to_srt() + '\n')
        
        return output_path
    
    def generate_from_audio_timestamps(
        self,
        timestamps: List[Tuple[float, float, str]],
        output_path: Path
    ) -> Path:
        """Генерация SRT из таймстемпов аудио (start, end, text)"""
        
        subtitles = []
        
        for i, (start, end, text) in enumerate(timestamps, 1):
            # Форматируем текст
            lines = self._split_into_chunks(text, 42)
            formatted_text = '\n'.join(lines[:2])
            
            subtitles.append(Subtitle(
                index=i,
                start_time=self._seconds_to_srt_time(start),
                end_time=self._seconds_to_srt_time(end),
                text=formatted_text
            ))
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sub in subtitles:
                f.write(sub.to_srt() + '\n')
        
        return output_path
    
    def adjust_timing(
        self,
        srt_path: Path,
        audio_duration: float,
        output_path: Path = None
    ) -> Path:
        """Корректировка тайминга под длительность аудио"""
        
        # Читаем существующий SRT
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Парсим субтитры
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if not matches:
            return srt_path
        
        # Находим текущую длительность
        last_end = self._srt_time_to_seconds(matches[-1][2])
        
        # Рассчитываем коэффициент масштабирования
        scale = audio_duration / last_end if last_end > 0 else 1
        
        # Корректируем тайминги
        subtitles = []
        for index, start, end, text in matches:
            new_start = self._srt_time_to_seconds(start) * scale
            new_end = self._srt_time_to_seconds(end) * scale
            
            subtitles.append(Subtitle(
                index=int(index),
                start_time=self._seconds_to_srt_time(new_start),
                end_time=self._seconds_to_srt_time(new_end),
                text=text.strip()
            ))
        
        # Записываем
        output = output_path or srt_path
        with open(output, 'w', encoding='utf-8') as f:
            for sub in subtitles:
                f.write(sub.to_srt() + '\n')
        
        return output
