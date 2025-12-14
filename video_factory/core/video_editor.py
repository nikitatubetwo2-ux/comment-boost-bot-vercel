"""
Видео редактор — монтаж с MoviePy
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import random
import numpy as np

# MoviePy 2.x imports
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, concatenate_audioclips, VideoFileClip,
    TextClip, ColorClip, VideoClip
)
from moviepy.video.fx import FadeIn, FadeOut, Resize
from PIL import Image, ImageFilter, ImageEnhance


@dataclass
class SceneConfig:
    """Конфигурация сцены"""
    image_path: Path
    duration: float
    start_time: float
    zoom_direction: str = "in"  # in, out, random
    pan_direction: str = "none"  # left, right, up, down, none


@dataclass
class VideoConfig:
    """Конфигурация видео"""
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    
    # Эффекты
    enable_zoom: bool = True
    min_zoom: float = 1.0
    max_zoom: float = 1.2
    zoom_speed: float = 0.5
    
    # Переходы
    transition_type: str = "fade"  # fade, dissolve, slide, none
    transition_duration: float = 0.5
    
    # Цветокоррекция
    color_grade: str = "none"  # none, cinematic, warm, cold, vintage, dramatic
    
    # Дополнительно
    add_vignette: bool = False
    add_film_grain: bool = False


@dataclass
class SubtitleStyle:
    """Стиль субтитров"""
    font: str = "Arial-Bold"
    font_size: int = 48
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 3
    bg_color: str = None  # None = прозрачный
    position: str = "bottom"  # bottom, center, top
    margin_bottom: int = 80


class VideoEditor:
    """Редактор видео"""
    
    def __init__(self, config: VideoConfig = None):
        self.config = config or VideoConfig()
        self.subtitle_style = SubtitleStyle()
    
    def create_ken_burns_clip(
        self,
        image_path: Path,
        duration: float,
        zoom_direction: str = "in"
    ) -> ImageClip:
        """Создание клипа с эффектом Ken Burns (зум + панорама)"""
        
        # Загружаем изображение
        img = Image.open(image_path)
        
        # Масштабируем под разрешение видео с запасом для зума
        target_w, target_h = self.config.resolution
        scale_factor = self.config.max_zoom * 1.1
        
        # Рассчитываем размер
        img_ratio = img.width / img.height
        target_ratio = target_w / target_h
        
        if img_ratio > target_ratio:
            new_h = int(target_h * scale_factor)
            new_w = int(new_h * img_ratio)
        else:
            new_w = int(target_w * scale_factor)
            new_h = int(new_w / img_ratio)
        
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Сохраняем временный файл
        temp_path = image_path.parent / f"_temp_{image_path.name}"
        img.save(temp_path)
        
        # Создаём клип
        clip = ImageClip(str(temp_path)).with_duration(duration)
        
        if self.config.enable_zoom:
            # Параметры зума
            start_zoom = self.config.min_zoom if zoom_direction == "in" else self.config.max_zoom
            end_zoom = self.config.max_zoom if zoom_direction == "in" else self.config.min_zoom
            
            # MoviePy 2.x: используем make_frame для Ken Burns эффекта
            original_frame = clip.get_frame(0)
            h, w = original_frame.shape[:2]
            
            def make_ken_burns_frame(t):
                progress = t / duration
                current_zoom = start_zoom + (end_zoom - start_zoom) * progress
                
                # Центрируем и обрезаем
                new_w = int(target_w / current_zoom)
                new_h = int(target_h / current_zoom)
                
                x1 = (w - new_w) // 2
                y1 = (h - new_h) // 2
                
                # Убеждаемся что не выходим за границы
                x1 = max(0, min(x1, w - new_w))
                y1 = max(0, min(y1, h - new_h))
                
                cropped = original_frame[y1:y1+new_h, x1:x1+new_w]
                
                # Масштабируем до целевого разрешения через PIL
                pil_img = Image.fromarray(cropped)
                pil_img = pil_img.resize(self.config.resolution, Image.Resampling.LANCZOS)
                return np.array(pil_img)
            
            # Создаём новый клип с функцией make_frame
            clip = VideoClip(make_ken_burns_frame, duration=duration)
            
            # Удаляем временный файл сразу после создания клипа
            # (данные уже в памяти в original_frame)
            if temp_path.exists():
                temp_path.unlink()
        else:
            # Если зум отключен, удаляем временный файл после создания клипа
            if temp_path.exists():
                temp_path.unlink()
        
        return clip.with_duration(duration)
    
    def apply_transition(
        self,
        clip1: ImageClip,
        clip2: ImageClip,
        transition_type: str = None
    ) -> List:
        """Применение перехода между клипами"""
        
        trans_type = transition_type or self.config.transition_type
        duration = self.config.transition_duration
        
        if trans_type == "none":
            return [clip1, clip2]
        
        if trans_type == "fade":
            clip1 = clip1.with_effects([FadeOut(duration)])
            clip2 = clip2.with_effects([FadeIn(duration)])
            # Накладываем конец первого на начало второго
            clip2 = clip2.with_start(clip1.duration - duration)
            return [clip1, clip2]
        
        if trans_type == "dissolve":
            # Плавное растворение
            clip1 = clip1.with_effects([FadeOut(duration)])
            clip2 = clip2.with_effects([FadeIn(duration)]).with_start(clip1.duration - duration)
            return [clip1, clip2]
        
        return [clip1, clip2]
    
    def apply_color_grade(self, clip, grade: str = None):
        """
        Применение цветокоррекции (MoviePy 2.x совместимо)
        
        Поддерживаемые стили:
        - cinematic: контраст + лёгкая десатурация
        - cinematic_bw: Ч/Б с высоким контрастом (для военной тематики)
        - dramatic: высокий контраст
        - vintage: тёплые тона, низкий контраст
        - warm/cold: цветовая температура
        """
        
        grade = grade or self.config.color_grade
        
        if grade == "none":
            return clip
        
        def color_filter(frame):
            img = Image.fromarray(frame)
            
            if grade == "cinematic":
                # Увеличиваем контраст, слегка синий оттенок
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.9)
            
            elif grade == "cinematic_bw":
                # Ч/Б с высоким контрастом — стиль военных документалок
                img = img.convert('L').convert('RGB')  # Ч/Б
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.3)  # Высокий контраст
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.05)  # Чуть светлее
            
            elif grade == "warm":
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.1)
                
            elif grade == "cold":
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.9)
            
            elif grade == "vintage":
                # Винтажный стиль — сепия + низкий контраст
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(0.9)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.7)
                # Добавляем тёплый оттенок
                r, g, b = img.split()
                r = r.point(lambda x: min(255, x + 20))
                b = b.point(lambda x: max(0, x - 10))
                img = Image.merge('RGB', (r, g, b))
            
            elif grade == "dramatic":
                # Высокий контраст для драматичных сцен
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.4)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.85)  # Слегка десатурация
            
            return np.array(img)
        
        # MoviePy 2.x: используем image_transform вместо fl_image
        return clip.image_transform(color_filter)
    
    def add_vignette(self, clip):
        """
        Добавление виньетки — затемнение по краям кадра
        Создаёт кинематографичный эффект фокуса на центре
        """
        
        def vignette_filter(frame):
            img = Image.fromarray(frame)
            width, height = img.size
            
            # Создаём радиальный градиент для виньетки
            vignette = Image.new('L', (width, height), 255)
            
            # Центр и радиус
            cx, cy = width // 2, height // 2
            max_dist = ((width/2)**2 + (height/2)**2) ** 0.5
            
            # Создаём градиент попиксельно (оптимизированно)
            for y in range(0, height, 2):  # Шаг 2 для скорости
                for x in range(0, width, 2):
                    dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
                    # Виньетка начинается с 60% от центра
                    factor = max(0, (dist / max_dist - 0.6) / 0.4)
                    darkness = int(255 * (1 - factor * 0.4))  # Максимум 40% затемнения
                    vignette.putpixel((x, y), darkness)
                    if x+1 < width:
                        vignette.putpixel((x+1, y), darkness)
                    if y+1 < height:
                        vignette.putpixel((x, y+1), darkness)
                        if x+1 < width:
                            vignette.putpixel((x+1, y+1), darkness)
            
            # Применяем виньетку
            vignette = vignette.filter(ImageFilter.GaussianBlur(radius=30))
            
            # Конвертируем в RGB и применяем
            r, g, b = img.split()
            r = Image.composite(r, Image.new('L', (width, height), 0), vignette)
            g = Image.composite(g, Image.new('L', (width, height), 0), vignette)
            b = Image.composite(b, Image.new('L', (width, height), 0), vignette)
            
            return np.array(Image.merge('RGB', (r, g, b)))
        
        return clip.image_transform(vignette_filter)
    
    def add_film_grain(self, clip, intensity: float = 0.05):
        """
        Добавление зернистости плёнки — аутентичный винтажный эффект
        Особенно хорошо для военной/исторической тематики
        """
        
        def grain_filter(frame):
            img = Image.fromarray(frame)
            width, height = img.size
            
            # Создаём шум
            noise = np.random.normal(0, intensity * 255, (height, width, 3))
            
            # Добавляем шум к изображению
            img_array = np.array(img).astype(np.float32)
            noisy = img_array + noise
            noisy = np.clip(noisy, 0, 255).astype(np.uint8)
            
            return noisy
        
        return clip.image_transform(grain_filter)
    
    def create_video(
        self,
        scenes: List[SceneConfig],
        audio_path: Path,
        output_path: Path,
        music_path: Optional[Path] = None,
        music_volume: float = 0.15
    ) -> Path:
        """Создание финального видео"""
        
        clips = []
        
        for i, scene in enumerate(scenes):
            # Определяем направление зума
            zoom_dir = scene.zoom_direction
            if zoom_dir == "random":
                zoom_dir = random.choice(["in", "out"])
            
            # Создаём клип
            clip = self.create_ken_burns_clip(
                scene.image_path,
                scene.duration,
                zoom_dir
            )
            
            clips.append(clip)
        
        # Применяем переходы
        if self.config.transition_type != "none" and len(clips) > 1:
            final_clips = [clips[0]]
            for i in range(1, len(clips)):
                transitioned = self.apply_transition(final_clips[-1], clips[i])
                final_clips = final_clips[:-1] + transitioned
            video = CompositeVideoClip(final_clips)
        else:
            video = concatenate_videoclips(clips, method="compose")
        
        # Применяем цветокоррекцию
        if self.config.color_grade and self.config.color_grade != "none":
            video = self.apply_color_grade(video)
        
        # Применяем виньетку (затемнение по краям)
        if self.config.add_vignette:
            video = self.add_vignette(video)
        
        # Применяем зернистость плёнки (для винтажного эффекта)
        if self.config.add_film_grain:
            video = self.add_film_grain(video, intensity=0.03)
        
        # Загружаем аудио
        voice_audio = AudioFileClip(str(audio_path))
        
        # Добавляем фоновую музыку
        if music_path and music_path.exists():
            music_audio = AudioFileClip(str(music_path))
            # Зацикливаем музыку если короче видео
            if music_audio.duration < video.duration:
                loops = int(video.duration / music_audio.duration) + 1
                music_audio = concatenate_audioclips([music_audio] * loops)
            music_audio = music_audio.subclip(0, video.duration)
            music_audio = music_audio.with_volume_scaled(music_volume)
            
            # Микшируем
            final_audio = CompositeAudioClip([voice_audio, music_audio])
        else:
            final_audio = voice_audio
        
        # Устанавливаем аудио
        video = video.with_audio(final_audio)
        
        # Рендерим
        video.write_videofile(
            str(output_path),
            fps=self.config.fps,
            codec='libx264',
            audio_codec='aac',
            bitrate='12M',
            threads=4
        )
        
        # Закрываем клипы
        video.close()
        voice_audio.close()
        
        return output_path
    
    def create_video_simple(
        self,
        images: List[Path],
        audio_path: Path,
        output_path: Path,
        music_path: Optional[Path] = None,
        music_volume: float = 0.15
    ) -> Path:
        """Упрощённое создание видео — автоматический расчёт длительности"""
        
        # Загружаем аудио для определения длительности
        audio = AudioFileClip(str(audio_path))
        total_duration = audio.duration
        audio.close()
        
        # Рассчитываем длительность каждой сцены
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
        
        return self.create_video(scenes, audio_path, output_path, music_path, music_volume)
    
    def create_quick_preview(
        self,
        images: List[Path],
        output_path: Path,
        audio_path: Optional[Path] = None,
        duration_per_image: float = 2.0,
        resolution: Tuple[int, int] = (1280, 720)
    ) -> Path:
        """
        Быстрое превью видео — для проверки ДО финального рендера
        
        Особенности:
        - Низкое разрешение (720p) для скорости
        - Простые переходы (fade)
        - Без Ken Burns эффекта
        - Рендер за 30-60 секунд вместо 10-15 минут
        
        Args:
            images: Список путей к изображениям
            output_path: Путь для сохранения превью
            audio_path: Опционально — аудио для синхронизации
            duration_per_image: Секунд на изображение (если нет аудио)
            resolution: Разрешение превью (по умолчанию 720p)
        """
        
        # Определяем длительность
        if audio_path and Path(audio_path).exists():
            audio = AudioFileClip(str(audio_path))
            total_duration = audio.duration
            duration_per_image = total_duration / len(images)
        else:
            audio = None
            total_duration = duration_per_image * len(images)
        
        clips = []
        
        for i, img_path in enumerate(images):
            if not Path(img_path).exists():
                continue
            
            # Загружаем и ресайзим изображение
            img = Image.open(img_path)
            
            # Масштабируем под разрешение
            img_ratio = img.width / img.height
            target_ratio = resolution[0] / resolution[1]
            
            if img_ratio > target_ratio:
                new_h = resolution[1]
                new_w = int(new_h * img_ratio)
            else:
                new_w = resolution[0]
                new_h = int(new_w / img_ratio)
            
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Центрируем и обрезаем
            left = (new_w - resolution[0]) // 2
            top = (new_h - resolution[1]) // 2
            img = img.crop((left, top, left + resolution[0], top + resolution[1]))
            
            # Сохраняем временный файл
            temp_path = Path(img_path).parent / f"_preview_temp_{i}.jpg"
            img.save(temp_path, quality=85)
            
            # Создаём клип
            clip = ImageClip(str(temp_path)).with_duration(duration_per_image)
            
            # Простой fade
            if i > 0:
                clip = clip.with_effects([FadeIn(0.3)])
            if i < len(images) - 1:
                clip = clip.with_effects([FadeOut(0.3)])
            
            clips.append(clip)
            
            # Удаляем временный файл
            if temp_path.exists():
                temp_path.unlink()
        
        # Собираем видео
        video = concatenate_videoclips(clips, method="compose")
        
        # Добавляем аудио если есть
        if audio:
            # Обрезаем аудио под длину видео
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            video = video.with_audio(audio)
        
        # Рендерим с низкими настройками для скорости
        video.write_videofile(
            str(output_path),
            fps=24,  # Меньше FPS для скорости
            codec='libx264',
            audio_codec='aac' if audio else None,
            bitrate='3M',  # Низкий битрейт
            preset='ultrafast',  # Самый быстрый пресет
            threads=4
        )
        
        # Закрываем
        video.close()
        if audio:
            audio.close()
        
        return output_path
    
    def create_slideshow_preview(
        self,
        images: List[Path],
        output_path: Path,
        fps: int = 1
    ) -> Path:
        """
        Супер-быстрое слайдшоу превью (без аудио)
        
        Для быстрой проверки изображений — 1 кадр в секунду
        Рендер за 5-10 секунд
        """
        
        clips = []
        
        for img_path in images:
            if not Path(img_path).exists():
                continue
            
            # Ресайзим для скорости
            img = Image.open(img_path)
            img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
            
            # Создаём фон и центрируем
            background = Image.new('RGB', (1280, 720), (0, 0, 0))
            offset = ((1280 - img.width) // 2, (720 - img.height) // 2)
            background.paste(img, offset)
            
            temp_path = Path(img_path).parent / f"_slide_{len(clips)}.jpg"
            background.save(temp_path, quality=80)
            
            clip = ImageClip(str(temp_path)).with_duration(1.0)
            clips.append(clip)
            
            temp_path.unlink()
        
        video = concatenate_videoclips(clips, method="compose")
        
        video.write_videofile(
            str(output_path),
            fps=fps,
            codec='libx264',
            bitrate='1M',
            preset='ultrafast',
            threads=4,
            audio=False
        )
        
        video.close()
        return output_path




    # === СУБТИТРЫ ===
    
    def create_subtitle_clip(self, text: str, duration: float, style: SubtitleStyle = None) -> TextClip:
        """Создание клипа с субтитрами"""
        style = style or self.subtitle_style
        
        # Разбиваем длинный текст на строки
        max_chars = 50
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        formatted_text = "\n".join(lines)
        
        txt_clip = TextClip(
            text=formatted_text,
            font=style.font,
            font_size=style.font_size,
            color=style.color,
            stroke_color=style.stroke_color,
            stroke_width=style.stroke_width,
            method='caption',
            size=(self.config.resolution[0] - 100, None)
        ).with_duration(duration)
        
        # Позиционируем
        if style.position == "bottom":
            txt_clip = txt_clip.with_position(('center', self.config.resolution[1] - style.margin_bottom - 60))
        elif style.position == "center":
            txt_clip = txt_clip.with_position('center')
        elif style.position == "top":
            txt_clip = txt_clip.with_position(('center', 50))
        
        return txt_clip
    
    def add_subtitles_to_video(self, video_path: Path, subtitles: List[Dict], 
                                output_path: Path, style: SubtitleStyle = None) -> Path:
        """Добавление субтитров к готовому видео"""
        style = style or self.subtitle_style
        
        video = VideoFileClip(str(video_path))
        subtitle_clips = []
        
        for sub in subtitles:
            text = sub.get('text', '')
            start = sub.get('start', 0)
            end = sub.get('end', start + 3)
            duration = end - start
            
            if not text.strip():
                continue
            
            txt_clip = self.create_subtitle_clip(text, duration, style)
            txt_clip = txt_clip.with_start(start)
            subtitle_clips.append(txt_clip)
        
        final = CompositeVideoClip([video] + subtitle_clips)
        
        final.write_videofile(
            str(output_path),
            fps=self.config.fps,
            codec='libx264',
            audio_codec='aac',
            bitrate='12M',
            threads=4
        )
        
        final.close()
        video.close()
        
        return output_path


def generate_subtitles_from_script(script: str, audio_duration: float) -> List[Dict]:
    """
    Генерация субтитров из сценария
    
    Args:
        script: Текст сценария
        audio_duration: Длительность аудио в секундах
    
    Returns:
        Список субтитров [{"text": "...", "start": 0.0, "end": 3.0}, ...]
    """
    import re
    
    # Убираем таймкоды и заголовки
    script = re.sub(r'\[[\d:]+\]', '', script)
    script = re.sub(r'\[ГЛАВА[^\]]*\]', '', script)
    script = re.sub(r'\[HOOK[^\]]*\]', '', script)
    script = re.sub(r'\[КУЛЬМИНАЦИЯ\]', '', script)
    script = re.sub(r'\[ЗАКЛЮЧЕНИЕ\]', '', script)
    
    # Разбиваем на предложения
    sentences = re.split(r'(?<=[.!?])\s+', script)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return []
    
    total_chars = sum(len(s) for s in sentences)
    subtitles = []
    current_time = 0.0
    
    for sentence in sentences:
        duration = (len(sentence) / total_chars) * audio_duration
        duration = max(1.5, min(duration, 8.0))
        
        subtitles.append({
            "text": sentence,
            "start": current_time,
            "end": current_time + duration
        })
        current_time += duration
    
    if subtitles and subtitles[-1]["end"] > audio_duration:
        subtitles[-1]["end"] = audio_duration
    
    return subtitles
