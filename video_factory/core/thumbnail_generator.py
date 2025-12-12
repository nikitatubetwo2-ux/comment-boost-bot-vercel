"""
Генератор превью для YouTube — AI создание кликабельных превью
"""

import requests
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ThumbnailResult:
    """Результат генерации превью"""
    concept: str
    path: Optional[Path]
    success: bool
    error: Optional[str] = None


class ThumbnailGenerator:
    """
    Генератор превью для YouTube
    
    Создаёт 3-5 вариантов превью для A/B тестирования
    Анализирует превью конкурентов для лучших результатов
    """
    
    BASE_URL = "https://image.pollinations.ai/prompt/"
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("output/thumbnails")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_thumbnail(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация одного превью (1280x720)"""
        try:
            # Добавляем параметры для превью
            full_prompt = f"{prompt}, youtube thumbnail style, eye-catching, vibrant colors, high contrast, professional"
            
            encoded = urllib.parse.quote(full_prompt)
            url = f"{self.BASE_URL}{encoded}?width=1280&height=720&nologo=true"
            
            response = requests.get(url, timeout=120)
            
            if response.status_code == 200 and len(response.content) > 1000:
                filepath = self.output_dir / f"{filename}.png"
                filepath.write_bytes(response.content)
                return ThumbnailResult(concept=prompt, path=filepath, success=True)
            else:
                return ThumbnailResult(concept=prompt, path=None, success=False, 
                                       error=f"HTTP {response.status_code}")
        except Exception as e:
            return ThumbnailResult(concept=prompt, path=None, success=False, error=str(e))
    
    def generate_variants(self, title: str, style: str = "", count: int = 3, 
                          save_prompts: bool = True) -> List[ThumbnailResult]:
        """
        Генерация нескольких вариантов превью
        
        Args:
            title: Заголовок видео
            style: Стиль (военный, исторический и т.д.)
            count: Количество вариантов
            save_prompts: Сохранять промпты в файл (для ручной генерации)
        """
        from core.groq_client import GroqClient
        from config import config
        import json
        
        if not config.api.groq_key:
            return []
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        # Генерируем промпты для превью
        prompts = self._generate_thumbnail_prompts(groq, title, style, count)
        
        # СОХРАНЯЕМ ПРОМПТЫ В ФАЙЛ (для ручной генерации в другой программе)
        if save_prompts and prompts:
            prompts_file = self.output_dir / "thumbnail_prompts.json"
            prompts_text_file = self.output_dir / "thumbnail_prompts.txt"
            
            # JSON для программной обработки
            prompts_file.write_text(json.dumps({
                "title": title,
                "style": style,
                "prompts": prompts
            }, ensure_ascii=False, indent=2))
            
            # TXT для удобного копирования
            txt_content = f"ПРЕВЬЮ ДЛЯ: {title}\n{'='*50}\n\n"
            for i, p in enumerate(prompts, 1):
                concept = p.get('concept', '') if isinstance(p, dict) else ''
                prompt = p.get('prompt_en', str(p)) if isinstance(p, dict) else str(p)
                text_overlay = p.get('text_overlay', '') if isinstance(p, dict) else ''
                
                txt_content += f"--- ВАРИАНТ {i} ---\n"
                txt_content += f"Концепция: {concept}\n"
                txt_content += f"Текст на превью: {text_overlay}\n"
                txt_content += f"ПРОМПТ:\n{prompt}\n\n"
            
            prompts_text_file.write_text(txt_content, encoding='utf-8')
        
        results = []
        for i, prompt_data in enumerate(prompts):
            prompt = prompt_data.get('prompt_en', '') if isinstance(prompt_data, dict) else str(prompt_data)
            concept = prompt_data.get('concept', f'Вариант {i+1}') if isinstance(prompt_data, dict) else f'Вариант {i+1}'
            
            # Пробуем сгенерировать через Pollinations
            result = self.generate_thumbnail(prompt, f"thumbnail_{i+1}")
            result.concept = concept
            results.append(result)
        
        return results
    
    def get_prompts_only(self, title: str, style: str = "", count: int = 3) -> List[Dict]:
        """
        Только генерация промптов БЕЗ картинок
        
        Для ручной генерации в Ideogram/Midjourney
        """
        from core.groq_client import GroqClient
        from config import config
        import json
        
        if not config.api.groq_key:
            return []
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        prompts = self._generate_thumbnail_prompts(groq, title, style, count)
        
        # Сохраняем в файл
        prompts_file = self.output_dir / "thumbnail_prompts.txt"
        
        txt_content = f"ПРЕВЬЮ ДЛЯ: {title}\n{'='*50}\n\n"
        for i, p in enumerate(prompts, 1):
            concept = p.get('concept', '') if isinstance(p, dict) else ''
            prompt = p.get('prompt_en', str(p)) if isinstance(p, dict) else str(p)
            
            txt_content += f"--- ВАРИАНТ {i}: {concept} ---\n"
            txt_content += f"{prompt}\n\n"
        
        prompts_file.write_text(txt_content, encoding='utf-8')
        
        return prompts
    
    def _generate_thumbnail_prompts(self, groq, title: str, style: str, count: int) -> List[Dict]:
        """Генерация промптов для превью через AI"""
        prompt = f"""Создай {count} РАЗНЫХ концепций превью для YouTube видео.

ЗАГОЛОВОК: {title}
СТИЛЬ: {style or 'документальный'}

Каждое превью должно быть КЛИКАБЕЛЬНЫМ:
- Яркие контрастные цвета
- Эмоциональное лицо или драматичная сцена
- Простая композиция (1-2 главных элемента)
- Интрига без спойлеров

Для каждого варианта создай:
1. Концепцию (что изображено)
2. Детальный промпт на английском для AI генератора

Ответь в JSON:
{{
    "thumbnails": [
        {{
            "concept": "Описание концепции на русском",
            "prompt_en": "Detailed English prompt for AI, youtube thumbnail style, dramatic lighting, vibrant colors, 8k, professional photography",
            "text_overlay": "Текст для наложения (2-3 слова)"
        }}
    ]
}}"""

        response = groq._chat([
            {"role": "system", "content": "Ты эксперт по YouTube превью с CTR 15%+. Создаёшь превью на которые невозможно не кликнуть."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            import json
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match).get('thumbnails', [])
        except:
            return []
    
    def analyze_competitor_thumbnails(self, video_urls: List[str]) -> Dict:
        """
        Анализ превью конкурентов
        
        Возвращает рекомендации по стилю превью
        """
        # TODO: Скачивание и AI анализ превью конкурентов
        return {
            "common_elements": ["яркие цвета", "лица", "текст"],
            "recommended_style": "dramatic, high contrast",
            "avoid": ["слишком много текста", "мелкие детали"]
        }


class ABThumbnailTester:
    """
    A/B тестирование превью — генерация нескольких вариантов для сравнения
    
    Создаёт 3-5 вариантов превью с разными концепциями:
    - Эмоциональное лицо
    - Драматичная сцена
    - Интригующий объект
    - Текстовый акцент
    - Контрастная композиция
    
    Сохраняет все промпты для ручной генерации в Ideogram/Midjourney
    """
    
    THUMBNAIL_STYLES = [
        {
            "name": "emotional_face",
            "description": "Крупный план эмоционального лица",
            "prompt_template": "extreme close-up portrait, {emotion} expression, dramatic lighting, cinematic, 8k, youtube thumbnail style, eye-catching"
        },
        {
            "name": "dramatic_scene",
            "description": "Драматичная сцена с действием",
            "prompt_template": "dramatic scene, {subject}, action shot, cinematic lighting, epic composition, 8k, youtube thumbnail style"
        },
        {
            "name": "mystery_object",
            "description": "Загадочный объект крупным планом",
            "prompt_template": "mysterious {object}, dramatic spotlight, dark background, intrigue, 8k, youtube thumbnail style, high contrast"
        },
        {
            "name": "split_composition",
            "description": "Разделённая композиция (до/после, противостояние)",
            "prompt_template": "split composition, {left_side} vs {right_side}, dramatic contrast, youtube thumbnail style, 8k"
        },
        {
            "name": "text_focus",
            "description": "Акцент на текстовом элементе",
            "prompt_template": "bold typography background, {theme} aesthetic, vibrant colors, youtube thumbnail style, space for text overlay"
        }
    ]
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("output/ab_thumbnails")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generator = ThumbnailGenerator(self.output_dir)
    
    def generate_ab_variants(self, title: str, topic: str, style: str = "",
                             count: int = 5, generate_images: bool = False) -> Dict:
        """
        Генерация A/B вариантов превью
        
        Args:
            title: Заголовок видео
            topic: Тема/описание видео
            style: Стиль (военный, исторический и т.д.)
            count: Количество вариантов (3-5)
            generate_images: Генерировать картинки через Pollinations (качество среднее)
        
        Returns:
            {
                "variants": [...],
                "prompts_file": "path/to/prompts.txt",
                "recommendation": "лучший вариант для данной темы"
            }
        """
        from core.groq_client import GroqClient
        from config import config
        import json
        
        if not config.api.groq_key:
            return {"error": "Groq API ключ не настроен"}
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        # Генерируем варианты через AI
        prompt = f"""Создай {count} РАЗНЫХ концепций превью для YouTube видео.

ЗАГОЛОВОК: {title}
ТЕМА: {topic}
СТИЛЬ: {style or 'документальный'}

Каждое превью должно использовать РАЗНЫЙ подход:
1. Эмоциональное лицо (крупный план с сильной эмоцией)
2. Драматичная сцена (действие, движение)
3. Загадочный объект (интрига, тайна)
4. Контрастная композиция (противопоставление)
5. Минималистичный дизайн (для текста)

Для КАЖДОГО варианта создай:
- Концепцию на русском
- Детальный промпт на английском (для AI генератора)
- Текст для наложения (2-4 слова, КЛИКБЕЙТ)
- Цветовую схему
- Оценку CTR потенциала (1-10)

Ответь в JSON:
{{
    "variants": [
        {{
            "id": 1,
            "style_type": "emotional_face",
            "concept_ru": "Описание концепции",
            "prompt_en": "Detailed English prompt, youtube thumbnail, 1280x720, vibrant colors, high contrast, professional, 8k",
            "text_overlay": "ШОКИРУЮЩАЯ ПРАВДА",
            "color_scheme": "тёмно-красный + золотой",
            "ctr_potential": 8,
            "why_works": "почему этот вариант привлечёт клики"
        }}
    ],
    "best_variant": 1,
    "recommendation": "общая рекомендация"
}}"""

        response = groq._chat([
            {"role": "system", "content": "Ты эксперт по YouTube превью с CTR 15%+. Создаёшь превью на которые невозможно не кликнуть. Знаешь психологию кликов."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            result = json.loads(json_match)
        except:
            result = {"variants": [], "error": "Не удалось распарсить ответ AI"}
        
        variants = result.get('variants', [])
        
        # Сохраняем промпты в файлы
        timestamp = int(time.time()) if 'time' in dir() else 0
        
        # JSON для программной обработки
        json_file = self.output_dir / f"ab_test_{timestamp}.json"
        json_file.write_text(json.dumps({
            "title": title,
            "topic": topic,
            "style": style,
            "variants": variants,
            "best_variant": result.get('best_variant'),
            "recommendation": result.get('recommendation')
        }, ensure_ascii=False, indent=2))
        
        # TXT для удобного копирования в Ideogram/Midjourney
        txt_file = self.output_dir / f"ab_test_{timestamp}.txt"
        txt_content = f"""A/B ТЕСТ ПРЕВЬЮ
{'='*60}
Заголовок: {title}
Тема: {topic}
{'='*60}

"""
        for v in variants:
            txt_content += f"""
--- ВАРИАНТ {v.get('id', '?')} ({v.get('style_type', 'unknown')}) ---
CTR потенциал: {v.get('ctr_potential', '?')}/10

Концепция: {v.get('concept_ru', '')}
Текст на превью: {v.get('text_overlay', '')}
Цвета: {v.get('color_scheme', '')}
Почему работает: {v.get('why_works', '')}

ПРОМПТ ДЛЯ КОПИРОВАНИЯ:
{v.get('prompt_en', '')}

"""
        
        txt_content += f"""
{'='*60}
РЕКОМЕНДАЦИЯ: Вариант #{result.get('best_variant', 1)}
{result.get('recommendation', '')}
"""
        
        txt_file.write_text(txt_content, encoding='utf-8')
        
        # Опционально генерируем картинки
        generated_images = []
        if generate_images:
            for v in variants:
                img_result = self.generator.generate_thumbnail(
                    v.get('prompt_en', ''),
                    f"variant_{v.get('id', 0)}"
                )
                if img_result.success:
                    generated_images.append({
                        "variant_id": v.get('id'),
                        "path": str(img_result.path)
                    })
        
        return {
            "variants": variants,
            "best_variant": result.get('best_variant'),
            "recommendation": result.get('recommendation'),
            "prompts_json": str(json_file),
            "prompts_txt": str(txt_file),
            "generated_images": generated_images,
            "tip": "Скопируйте промпты из TXT файла в Ideogram или Midjourney для лучшего качества"
        }
    
    def compare_thumbnails(self, image_paths: List[Path]) -> Dict:
        """
        AI сравнение готовых превью
        
        Анализирует загруженные превью и даёт рекомендации
        """
        # TODO: Интеграция с vision моделью для анализа изображений
        return {
            "status": "not_implemented",
            "tip": "Функция сравнения превью будет добавлена с поддержкой vision моделей"
        }


# Импорт time для timestamp
import time


class TrendAnalyzer:
    """
    Анализатор трендов — находит темы ДО того как они взорвутся
    """
    
    def __init__(self):
        pass
    
    def get_rising_topics(self, niche: str, days: int = 7) -> List[Dict]:
        """
        Поиск растущих тем в нише
        
        Анализирует:
        - Новые видео с быстрым ростом просмотров
        - Google Trends
        - Новости по теме
        """
        from core.groq_client import GroqClient
        from config import config
        
        if not config.api.groq_key:
            return []
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        prompt = f"""Ты аналитик YouTube трендов. Предскажи какие темы в нише "{niche}" будут популярны в ближайшую неделю.

Учитывай:
- Годовщины исторических событий
- Текущие мировые события связанные с нишей
- Сезонность (время года, праздники)
- Паттерны популярности в этой нише

Предложи 5 тем которые СЕЙЧАС имеют потенциал стать вирусными.

Ответь в JSON:
{{
    "trending_topics": [
        {{
            "topic": "тема",
            "why_trending": "почему актуально сейчас",
            "viral_potential": 85,
            "best_angle": "лучший угол подачи",
            "urgency": "высокая/средняя/низкая"
        }}
    ]
}}"""

        response = groq._chat([
            {"role": "system", "content": "Ты эксперт по YouTube трендам и вирусному контенту."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            import json
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match).get('trending_topics', [])
        except:
            return []
    
    def predict_virality(self, title: str, niche: str) -> Dict:
        """
        Предсказание вирусности темы
        
        Возвращает оценку и рекомендации
        """
        from core.groq_client import GroqClient
        from config import config
        
        if not config.api.groq_key:
            return {"score": 50, "recommendations": []}
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        prompt = f"""Оцени вирусный потенциал этого видео:

ЗАГОЛОВОК: {title}
НИША: {niche}

Оцени по критериям:
1. Эмоциональный отклик (0-100)
2. Уникальность темы (0-100)
3. Актуальность (0-100)
4. Кликабельность заголовка (0-100)

Дай общую оценку и рекомендации по улучшению.

Ответь в JSON:
{{
    "scores": {{
        "emotional": 75,
        "uniqueness": 60,
        "relevance": 80,
        "clickability": 70
    }},
    "total_score": 71,
    "verdict": "хороший потенциал / средний / низкий",
    "recommendations": ["рекомендация 1", "рекомендация 2"],
    "improved_title": "улучшенный заголовок если нужно"
}}"""

        response = groq._chat([
            {"role": "system", "content": "Ты эксперт по вирусному YouTube контенту с опытом анализа миллионов видео."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            import json
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"total_score": 50, "recommendations": []}
