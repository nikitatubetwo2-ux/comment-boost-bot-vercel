"""
Клиент Groq API для генерации текста
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
from groq import Groq


@dataclass
class AnalysisResult:
    """Результат анализа"""
    triggers: Dict[str, List[str]]
    style: Dict[str, str]
    recommendations: List[str]


class GroqClient:
    """Клиент для работы с Groq API"""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model = model
    
    def _chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Базовый метод для чата"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def chat(self, prompt: str, system: str = "Ты полезный AI ассистент.", temperature: float = 0.7) -> str:
        """Простой чат с одним промптом"""
        return self._chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ], temperature=temperature)
    
    def analyze_titles(self, titles: List[str]) -> Dict[str, Any]:
        """Анализ заголовков видео — выявление триггеров"""
        prompt = f"""Проанализируй эти заголовки YouTube видео и выяви паттерны/триггеры, которые привлекают внимание:

ЗАГОЛОВКИ:
{chr(10).join(f'- {t}' for t in titles[:30])}

Ответь в JSON формате:
{{
    "triggers": {{
        "numbers": ["примеры использования чисел"],
        "emotions": ["эмоциональные слова"],
        "questions": ["вопросительные конструкции"],
        "intrigue": ["интригующие элементы"],
        "urgency": ["элементы срочности"]
    }},
    "patterns": ["общие паттерны построения заголовков"],
    "effective_words": ["самые эффективные слова"],
    "title_structure": "описание типичной структуры заголовка"
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по YouTube SEO и психологии заголовков. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            # Извлекаем JSON из ответа
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"raw_analysis": response}
    
    def analyze_style(self, descriptions: List[str], titles: List[str]) -> Dict[str, Any]:
        """Анализ стиля контента"""
        prompt = f"""Проанализируй стиль YouTube канала на основе заголовков и описаний:

ЗАГОЛОВКИ:
{chr(10).join(f'- {t}' for t in titles[:20])}

ОПИСАНИЯ (первые 500 символов каждого):
{chr(10).join(f'---{chr(10)}{d[:500]}' for d in descriptions[:10])}

Определи:
1. Стиль повествования (документальный, развлекательный, образовательный)
2. Тон (серьёзный, лёгкий, драматичный)
3. Целевая аудитория
4. Уникальные особенности подачи
5. Рекомендуемый голос для озвучки

Ответь в JSON:
{{
    "narrative_style": "стиль повествования",
    "tone": "тон",
    "target_audience": "целевая аудитория",
    "unique_features": ["особенности"],
    "recommended_voice": {{
        "gender": "мужской/женский",
        "type": "тип голоса",
        "pace": "темп речи",
        "emotion": "эмоциональность"
    }},
    "content_structure": "как обычно структурирован контент"
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по контент-анализу YouTube. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"raw_analysis": response}
    
    def generate_subniche(self, main_topic: str, competitor_info: str) -> Dict[str, Any]:
        """
        Генерация подниши с ДЕТАЛЬНЫМ анализом:
        - Поисковый спрос (интерес аудитории)
        - Уровень конкуренции
        - Потенциал роста
        """
        prompt = f"""Проведи ГЛУБОКИЙ анализ и найди ЗОЛОТУЮ поднишу для YouTube канала.

ОСНОВНАЯ ТЕМА КОНКУРЕНТА: {main_topic}

ИНФОРМАЦИЯ О КОНКУРЕНТЕ:
{competitor_info}

=== КРИТЕРИИ ИДЕАЛЬНОЙ ПОДНИШИ ===

1. ВЫСОКИЙ ПОИСКОВЫЙ СПРОС:
   - Люди активно ищут эту тему
   - Есть постоянный интерес (не сезонный)
   - Тема вызывает эмоции (страх, любопытство, восхищение)

2. НИЗКАЯ КОНКУРЕНЦИЯ:
   - Мало качественных каналов на эту тему
   - Большие каналы не фокусируются на этом
   - Есть пространство для нового игрока

3. ПОТЕНЦИАЛ ВИРУСНОСТИ:
   - Темы легко делать кликбейтными (честно)
   - Контент хочется поделиться
   - Вызывает обсуждения в комментариях

4. МОНЕТИЗАЦИЯ:
   - Аудитория платёжеспособная
   - Есть потенциал для спонсоров
   - Длинные видео (больше рекламы)

=== ЗАДАЧА ===

Придумай 5 КОНКРЕТНЫХ подниш с детальным анализом каждой.

Ответь в JSON:
{{
    "subniches": [
        {{
            "name": "КОНКРЕТНОЕ название подниши",
            "description": "подробное описание что это за подниша",
            "search_demand": {{
                "score": 8,
                "reasoning": "почему высокий спрос",
                "search_queries": ["примеры поисковых запросов"]
            }},
            "competition": {{
                "score": 3,
                "reasoning": "почему низкая конкуренция",
                "main_competitors": ["кто уже делает"]
            }},
            "viral_potential": {{
                "score": 9,
                "reasoning": "почему будет вирусится"
            }},
            "why_works": "ДЕТАЛЬНОЕ объяснение почему эта подниша сработает",
            "example_topics": ["5 конкретных тем для видео"],
            "target_audience": "кто будет смотреть",
            "growth_potential": "потенциал роста канала"
        }}
    ],
    "recommended": "какую поднишу рекомендуешь и ПОЧЕМУ (детально)",
    "analysis_summary": "общий вывод по анализу ниши"
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты креативный стратег YouTube контента. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"raw_analysis": response}
    
    def generate_video_topics(self, subniche: str, style_info: str, count: int = 5, 
                               excluded_topics: List[str] = None, variation_seed: int = 0) -> List[Dict]:
        """
        Генерация тем для видео с максимальным разнообразием
        
        Args:
            subniche: Подниша канала
            style_info: Информация о стиле
            count: Количество тем
            excluded_topics: Темы которые уже были (не повторять)
            variation_seed: Для разнообразия при повторных запросах
        """
        import random
        
        # Разные углы подачи для разнообразия
        angles = [
            "малоизвестные факты и секреты",
            "шокирующие истории и события", 
            "личные истории героев",
            "загадки и тайны",
            "сравнения и противостояния",
            "хронология событий",
            "мифы и их разоблачение",
            "забытые страницы истории"
        ]
        
        # Выбираем случайные углы
        random.seed(variation_seed if variation_seed else None)
        selected_angles = random.sample(angles, min(3, len(angles)))
        
        excluded_str = ""
        if excluded_topics:
            excluded_str = f"""
НЕ ПРЕДЛАГАТЬ ЭТИ ТЕМЫ (уже были):
{chr(10).join(f'- {t}' for t in excluded_topics[-20:])}
"""
        
        prompt = f"""Сгенерируй {count} УНИКАЛЬНЫХ тригерных тем для YouTube видео.

ПОДНИША: {subniche}

СТИЛЬ КАНАЛА:
{style_info}

ОБЯЗАТЕЛЬНО используй разные УГЛЫ ПОДАЧИ:
{chr(10).join(f'- {a}' for a in selected_angles)}
{excluded_str}
ВАЖНО:
- Каждая тема должна быть УНИКАЛЬНОЙ
- Используй разные форматы заголовков (вопросы, утверждения, списки)
- Темы должны вызывать РАЗНЫЕ эмоции (страх, удивление, любопытство, восхищение)
- Не повторяй структуру заголовков

Для каждой темы создай:
1. Кликбейтный (но честный) заголовок — РАЗНЫЕ ФОРМАТЫ
2. Уникальный угол подачи
3. Почему эта тема зацепит зрителя
4. Оценка вирусного потенциала (1-10)

Ответь в JSON:
{{
    "topics": [
        {{
            "title": "заголовок",
            "hook": "интригующий хук для начала",
            "description": "о чём видео",
            "angle": "угол подачи",
            "viral_potential": 8,
            "why_works": "почему сработает",
            "target_emotion": "какую эмоцию вызывает"
        }}
    ]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по вирусному YouTube контенту. Создавай РАЗНООБРАЗНЫЕ темы с разными углами подачи. Никогда не повторяйся! Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ], temperature=0.9)  # Высокая температура для разнообразия
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match).get('topics', [])
        except:
            return [{"raw": response}]
    
    def generate_script(self, topic: str, duration: str, style: str, include_hooks: bool = True) -> str:
        """Генерация сценария — УВЕЛИЧЕННЫЙ ОБЪЁМ"""
        # Расчёт: ~150 слов/минута для комфортной озвучки
        duration_map = {
            "10-20 минут": (2500, 15),
            "20-30 минут": (4000, 25),
            "30-40 минут": (5500, 35),
            "40-50 минут": (7000, 45),
            "50-60 минут": (9000, 55),
            "60+ минут": (10000, 65)
        }
        
        words, mins = duration_map.get(duration, (4000, 25))
        
        prompt = f"""Напиши ПОЛНЫЙ РАЗВЁРНУТЫЙ сценарий для YouTube видео.

ТЕМА: {topic}
ДЛИТЕЛЬНОСТЬ: {mins} минут
ТРЕБУЕМЫЙ ОБЪЁМ: МИНИМУМ {words} слов (это критически важно!)

СТИЛЬ: {style}

СТРУКТУРА СЦЕНАРИЯ:

[HOOK - 0:00-0:45]
Мощное начало без приветствий. Сразу интрига, факт или вопрос который заставит остаться.

[ГЛАВА 1: Название - 0:45-X:XX]
Развёрнутое повествование с деталями, примерами, описаниями.

[ГЛАВА 2: Название - X:XX-X:XX]
...продолжение истории...

[ГЛАВА 3-N: ...]
...столько глав сколько нужно для полного раскрытия темы...

[КУЛЬМИНАЦИЯ]
Самый напряжённый момент истории.

[ЗАКЛЮЧЕНИЕ]
Выводы, мораль, призыв подписаться.

КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
1. НЕ ПИШИ "Привет", "Добро пожаловать" — сразу в тему!
2. МИНИМУМ {words} слов — это обязательно!
3. Каждая глава должна быть РАЗВЁРНУТОЙ (минимум 500-800 слов)
4. Добавляй детали, описания, эмоции, диалоги
5. Используй риторические вопросы каждые 2-3 абзаца
6. Интрига перед каждой новой главой
7. Текст для ОЗВУЧКИ — должен звучать естественно

ПИШИ ПОЛНОСТЬЮ, БЕЗ СОКРАЩЕНИЙ, БЕЗ "..." или "и так далее".
Каждое предложение должно быть написано полностью."""

        response = self._chat([
            {"role": "system", "content": f"Ты профессиональный сценарист документальных YouTube видео. Стиль: {style}. Пишешь ДЛИННЫЕ, ДЕТАЛЬНЫЕ сценарии которые полностью раскрывают тему. Никогда не сокращаешь текст."},
            {"role": "user", "content": prompt}
        ], temperature=0.8, max_tokens=8000)
        
        return response
    
    def generate_preview_prompts(self, title: str, style_info: str) -> List[Dict]:
        """Генерация 3 промптов для превью"""
        prompt = f"""Создай 3 детальных промпта для генерации превью YouTube видео.

ЗАГОЛОВОК ВИДЕО: {title}

СТИЛЬ КАНАЛА:
{style_info}

Каждый промпт должен быть МАКСИМАЛЬНО детальным для AI генератора изображений:
- Точная композиция
- Цветовая схема
- Расположение элементов
- Стиль (реалистичный, иллюстрация и т.д.)
- Эмоциональный посыл
- Текст на превью (2-3 слова максимум)

Ответь в JSON:
{{
    "prompts": [
        {{
            "concept": "концепция превью",
            "prompt_en": "детальный промпт на английском для AI",
            "text_overlay": "текст для наложения",
            "text_position": "где разместить текст",
            "color_scheme": "цветовая схема",
            "style": "стиль изображения"
        }}
    ]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по YouTube превью с CTR 15%+. Создаёшь превью, на которые невозможно не кликнуть. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match).get('prompts', [])
        except:
            return [{"raw": response}]
    
    def generate_image_prompts_batch(self, script: str, style: str, 
                                      duration_minutes: int = 25, batch_size: int = 15) -> List[Dict]:
        """
        BATCH генерация промптов — все промпты за 1-2 запроса
        
        Оптимизация: вместо генерации по одному, генерируем пачками по 15-20 штук.
        Это в 3-5 раз быстрее чем последовательная генерация.
        """
        # Расчёт количества изображений
        images_first_5min = 25
        remaining_minutes = max(0, duration_minutes - 5)
        images_after_5min = int(remaining_minutes * 60 / 40)
        total_images = images_first_5min + images_after_5min
        
        all_prompts = []
        
        # Разбиваем на батчи
        batches_needed = (total_images + batch_size - 1) // batch_size
        
        for batch_idx in range(batches_needed):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_images)
            count_in_batch = end_idx - start_idx
            
            # Определяем какая часть сценария для этого батча
            script_part = script[start_idx * 200:(end_idx + 5) * 200]  # ~200 символов на сцену
            
            batch_prompts = self._generate_prompts_batch(
                script_part, style, count_in_batch, start_idx, total_images
            )
            all_prompts.extend(batch_prompts)
        
        return all_prompts[:total_images]
    
    def _generate_prompts_batch(self, script_part: str, style: str, 
                                 count: int, start_idx: int, total: int) -> List[Dict]:
        """Генерация одного батча промптов"""
        prompt = f"""Создай {count} детальных промптов для AI генерации изображений.

ЧАСТЬ СЦЕНАРИЯ:
{script_part[:3000]}

СТИЛЬ: {style}

Это изображения #{start_idx+1}-{start_idx+count} из {total}.

ТРЕБОВАНИЯ:
1. Для людей: "anatomically correct, natural facial features"
2. Качество: "masterpiece, 8k, sharp focus, cinematic"
3. Каждый промпт уникален и соответствует сцене

Ответь в JSON:
{{
    "scenes": [
        {{
            "id": {start_idx+1},
            "prompt_en": "detailed English prompt for AI"
        }}
    ]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты prompt engineer для AI изображений. Отвечай только JSON."},
            {"role": "user", "content": prompt}
        ], max_tokens=4000)
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match).get('scenes', [])
        except:
            return []
    
    def generate_image_prompts(self, script: str, style: str, duration_minutes: int = 25) -> List[Dict]:
        """
        Генерация промптов для изображений с ПРАВИЛЬНЫМ ТАЙМИНГОМ:
        - Первые 5 минут: картинка каждые 10-15 секунд (для удержания)
        - После 5 минут: картинка каждые 40 секунд
        
        Каждая картинка будет с эффектом приближения/отдаления (Ken Burns)
        """
        # Расчёт количества изображений
        # Первые 5 минут = 300 сек / 12 сек = ~25 картинок
        # Остальное время = (duration - 5) * 60 / 40 сек
        images_first_5min = 25  # ~12 сек на картинку
        remaining_minutes = max(0, duration_minutes - 5)
        images_after_5min = int(remaining_minutes * 60 / 40)
        total_images = images_first_5min + images_after_5min
        
        prompt = f"""Создай {total_images} детальных промптов для AI генерации изображений к видео.

СЦЕНАРИЙ:
{script[:10000]}

СТИЛЬ: {style}

=== ВАЖНО: ТАЙМИНГ ИЗОБРАЖЕНИЙ ===
Первые 5 минут видео (0:00-5:00): картинка меняется каждые 10-15 секунд
- Нужно ~25 изображений для первых 5 минут
- Частая смена для удержания внимания зрителя

После 5 минут: картинка меняется каждые 40 секунд
- Нужно ~{images_after_5min} изображений для остального времени
- Зритель уже вовлечён, можно реже менять

=== ЭФФЕКТЫ ДВИЖЕНИЯ (Ken Burns) ===
Для каждой картинки укажи эффект:
- "zoom_in" — приближение (для драматичных моментов)
- "zoom_out" — отдаление (для панорамных сцен)
- "pan_left" / "pan_right" — панорама
- "static" — статично (редко)

=== ТРЕБОВАНИЯ К КАЧЕСТВУ ===
1. Для людей: "anatomically correct, natural facial features, proper proportions"
2. Качество: "masterpiece, 8k, sharp focus, cinematic lighting"
3. Стиль: "documentary photograph, Kodachrome film, historical accuracy"

СТРУКТУРА ПРОМПТА:
[Кто/что] + [детали внешности] + [одежда] + [действие] + [место] + [освещение] + [качество теги]

Ответь в JSON:
{{
    "scenes": [
        {{
            "id": 1,
            "timecode": "0:00-0:12",
            "duration_sec": 12,
            "scene_ru": "описание на русском",
            "prompt_en": "детальный промпт на английском",
            "motion_effect": "zoom_in",
            "is_first_5min": true
        }}
    ]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты профессиональный prompt engineer для AI генерации изображений. Создаёшь промпты которые дают КАЧЕСТВЕННЫЕ результаты без дефектов: правильная анатомия людей, чёткие детали, без искажений. Специализируешься на исторических сценах. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ], max_tokens=8000)
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match).get('scenes', [])
        except:
            return [{"raw": response}]
    
    def improve_failed_prompt(self, original_prompt: str, error: str = "") -> str:
        """Улучшение промпта который не сработал"""
        prompt = f"""Этот промпт для генерации изображения не сработал. Перепиши его.

ОРИГИНАЛЬНЫЙ ПРОМПТ:
{original_prompt}

ОШИБКА: {error if error else "Не удалось сгенерировать"}

ТРЕБОВАНИЯ К НОВОМУ ПРОМПТУ:
1. Упрости сложные элементы
2. Убери потенциально проблемные слова (насилие, кровь и т.д.)
3. Сохрани основную идею сцены
4. Добавь "digital art, illustration" вместо "photorealistic" если было
5. Сделай промпт более универсальным

Ответь ТОЛЬКО новым промптом на английском, без объяснений."""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по промптам для AI генерации. Исправляешь проблемные промпты."},
            {"role": "user", "content": prompt}
        ], temperature=0.5, max_tokens=500)
        
        return response.strip()
    
    def analyze_niche(self, query: str, channels_info: str) -> Dict[str, Any]:
        """AI анализ ниши - поиск подниш с низкой конкуренцией"""
        prompt = f"""Проанализируй нишу YouTube и найди возможности.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {query}

НАЙДЕННЫЕ КАНАЛЫ В НИШЕ:
{channels_info}

ЗАДАЧА:
1. Оцени насыщенность ниши (много ли конкурентов)
2. Найди 5 ПОДНИШ с низкой конкуренцией но высоким потенциалом
3. Для каждой подниши объясни почему она перспективна
4. Предложи уникальный угол подачи

Ответь в JSON:
{{
    "niche_analysis": {{
        "saturation": "низкая/средняя/высокая",
        "saturation_score": 75,
        "main_competitors": 3,
        "opportunity_score": 80,
        "summary": "краткий вывод о нише"
    }},
    "subniches": [
        {{
            "name": "название подниши",
            "competition": "низкая/средняя",
            "potential": "высокий/средний",
            "why_works": "почему это сработает",
            "unique_angle": "уникальный угол подачи",
            "example_topics": ["тема 1", "тема 2", "тема 3"],
            "target_audience": "целевая аудитория"
        }}
    ],
    "recommendation": "какую поднишу рекомендуешь и почему",
    "strategy": "стратегия входа в нишу"
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по YouTube стратегии и анализу ниш. Находишь золотые возможности где мало конкуренции но много потенциала. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ], max_tokens=4000)
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"raw_analysis": response}
    
    def generate_seo(self, title: str, script: str, competitor_tags: List[str], 
                     subniche: str = "", channel_keywords: List[str] = None) -> Dict[str, Any]:
        """
        Генерация SEO: описание, теги, хештеги
        
        Расширенный анализ:
        - Теги конкурентов
        - Ключевые слова ниши
        - Популярные поисковые запросы
        - Хештеги с высоким охватом
        """
        keywords_str = ', '.join(channel_keywords[:20]) if channel_keywords else ''
        
        prompt = f"""Создай ПРОФЕССИОНАЛЬНУЮ SEO оптимизацию для YouTube видео.

ЗАГОЛОВОК: {title}

ПОДНИША КАНАЛА: {subniche}

СЦЕНАРИЙ (начало):
{script[:3000]}

ТЕГИ КОНКУРЕНТОВ:
{', '.join(competitor_tags[:30])}

КЛЮЧЕВЫЕ СЛОВА КАНАЛА:
{keywords_str}

=== ЗАДАЧИ ===

1. ОПИСАНИЕ (2000-3000 символов):
   - Первые 150 символов — самые важные (видны в поиске)
   - Ключевые слова в первых 2-3 предложениях
   - Таймкоды для навигации
   - Призыв к действию (подписка, лайк)
   - Ссылки на соцсети (плейсхолдеры)

2. ТЕГИ (30 штук, СТРАТЕГИЯ):
   - 5 высокочастотных (100K+ запросов) — для охвата
   - 10 среднечастотных (10K-100K) — баланс
   - 10 низкочастотных (1K-10K) — точное попадание
   - 5 длинных фраз (long-tail) — конверсия

3. ХЕШТЕГИ (5 штук):
   - Только популярные с высоким охватом
   - Релевантные теме видео
   - Микс общих и нишевых

4. АЛЬТЕРНАТИВНЫЕ ЗАГОЛОВКИ (3 штуки):
   - Разные триггеры (вопрос, число, интрига)
   - A/B тест варианты

Ответь в JSON:
{{
    "description": "полное описание с таймкодами и призывами",
    "tags": ["тег1", "тег2", ...],
    "tags_strategy": {{
        "high_volume": ["теги с высоким объёмом"],
        "medium_volume": ["средние"],
        "low_volume": ["низкие но точные"],
        "long_tail": ["длинные фразы"]
    }},
    "hashtags": ["#хештег1", ...],
    "seo_title_alternatives": ["вариант1", "вариант2", "вариант3"],
    "first_comment": "текст для закреплённого комментария"
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты SEO специалист YouTube с опытом продвижения каналов-миллионников. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"raw": response}

    def generate_synced_content(self, topic: str, duration: str, style: str) -> Dict[str, Any]:
        """
        Генерация сценария с синхронизацией картинка-текст
        
        Возвращает:
        - script: полный текст сценария
        - segments: список сегментов с таймкодами и промптами для картинок
        
        Первые 5 минут: картинка каждые 10-15 сек
        После 5 минут: картинка каждые 30-40 сек
        """
        duration_map = {
            "10-20 минут": (2500, 15),
            "20-30 минут": (4000, 25),
            "30-40 минут": (5500, 35),
            "40-50 минут": (7000, 45),
            "50-60 минут": (9000, 55),
            "60+ минут": (10000, 65)
        }
        
        words, mins = duration_map.get(duration, (4000, 25))
        
        prompt = f"""Создай сценарий для YouTube видео с СИНХРОНИЗАЦИЕЙ текста и изображений.

ТЕМА: {topic}
ДЛИТЕЛЬНОСТЬ: {mins} минут
ОБЪЁМ: минимум {words} слов
СТИЛЬ: {style}

ВАЖНО: Раздели сценарий на СЕГМЕНТЫ. Каждый сегмент = одна картинка + текст озвучки.

ПРАВИЛА СЕГМЕНТАЦИИ:
- Первые 5 минут (0:00-5:00): сегменты по 10-15 секунд (частая смена картинок для удержания)
- После 5 минут: сегменты по 30-40 секунд

Для каждого сегмента укажи:
1. Таймкод начала и конца
2. Текст для озвучки (что говорит диктор)
3. Промпт для изображения (на английском, детальный)

НЕ ПИШИ приветствия! Сразу в тему с интригой.

Ответь в JSON:
{{
    "title": "заголовок видео",
    "total_words": число,
    "segments": [
        {{
            "id": 1,
            "start": "0:00",
            "end": "0:12",
            "text": "Текст для озвучки этого сегмента...",
            "image_prompt": "Detailed English prompt for AI image generation, cinematic, 8k..."
        }},
        {{
            "id": 2,
            "start": "0:12",
            "end": "0:25",
            "text": "Следующий текст...",
            "image_prompt": "Next scene prompt..."
        }}
    ]
}}

Создай ВСЕ сегменты для полного видео на {mins} минут!"""

        response = self._chat([
            {"role": "system", "content": f"Ты профессиональный сценарист документальных YouTube видео. Стиль: {style}. Создаёшь детальные сценарии с синхронизацией аудио и видео."},
            {"role": "user", "content": prompt}
        ], temperature=0.8, max_tokens=8000)
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            data = json.loads(json_match)
            
            # Собираем полный текст сценария
            full_script = ""
            for seg in data.get('segments', []):
                full_script += seg.get('text', '') + "\n\n"
            
            data['full_script'] = full_script.strip()
            return data
            
        except:
            return {"error": "Failed to parse", "raw": response}
    
    def generate_more_subniches(self, main_niche: str, rejected: List[str], style_context: str) -> List[Dict]:
        """
        Генерация новых подниш (исключая отклонённые)
        
        Используется когда пользователь отклонил предложенные подниши
        """
        prompt = f"""Предложи 5 НОВЫХ подниш для YouTube канала.

ОСНОВНАЯ НИША: {main_niche}

УЖЕ ОТКЛОНЁННЫЕ ПОДНИШИ (НЕ ПРЕДЛАГАТЬ):
{chr(10).join(f'- {r}' for r in rejected)}

КОНТЕКСТ КАНАЛА:
{style_context}

Предложи ДРУГИЕ подниши, которые:
1. Связаны с основной нишей
2. Имеют низкую конкуренцию
3. Интересны аудитории
4. НЕ повторяют отклонённые

Ответь в JSON:
{{
    "subniches": [
        {{
            "name": "название",
            "description": "описание",
            "competition": "низкая/средняя",
            "potential": "высокий/средний",
            "example_topics": ["тема 1", "тема 2", "тема 3"]
        }}
    ]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты креативный стратег YouTube. Находишь уникальные ниши. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match).get('subniches', [])
        except:
            return []

    def analyze_competitor_voice(self, channel_name: str, video_titles: List[str], 
                                  descriptions: List[str]) -> Dict[str, Any]:
        """
        Анализ голоса/стиля озвучки конкурента для подбора похожего голоса
        
        На основе контента определяем:
        - Пол диктора
        - Возраст (молодой/средний/старший)
        - Тон (серьёзный/casual/драматичный)
        - Скорость речи
        - Эмоциональность
        """
        prompt = f"""Проанализируй стиль озвучки YouTube канала на основе его контента.

КАНАЛ: {channel_name}

ЗАГОЛОВКИ ВИДЕО:
{chr(10).join(f'- {t}' for t in video_titles[:15])}

ОПИСАНИЯ:
{chr(10).join(f'---{chr(10)}{d[:300]}' for d in descriptions[:5])}

На основе тематики и стиля контента определи, какой голос скорее всего используется:

1. Пол диктора (male/female) — исходя из тематики
2. Возраст голоса (young/middle/old) — молодой энергичный, средний профессиональный, старший авторитетный
3. Тон (serious/casual/dramatic) — серьёзный документальный, лёгкий разговорный, драматичный напряжённый
4. Скорость речи (slow/medium/fast) — медленная вдумчивая, средняя, быстрая энергичная
5. Эмоциональность (calm/energetic/dramatic) — спокойная, энергичная, драматичная

Ответь в JSON:
{{
    "gender": "male",
    "age": "middle",
    "tone": "serious",
    "speed": "medium",
    "emotion": "dramatic",
    "reasoning": "почему такой выбор",
    "voice_description": "описание идеального голоса для этого контента"
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по голосовому брендингу и озвучке. Анализируешь контент и определяешь оптимальный голос."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            # Дефолт для военной тематики
            return {
                "gender": "male",
                "age": "middle", 
                "tone": "serious",
                "speed": "medium",
                "emotion": "dramatic",
                "reasoning": "Военная/историческая тематика требует серьёзного мужского голоса"
            }
    
    def analyze_hooks(self, video_titles: List[str], video_descriptions: List[str]) -> Dict[str, Any]:
        """
        Анализ крючков (hooks) из топовых видео конкурента
        
        Анализирует первые 30 секунд видео (по описаниям и заголовкам)
        и создаёт мощный hook для нового видео.
        
        Правила хорошего hook:
        - Никаких приветствий и вступлений
        - Сразу интрига, факт или вопрос
        - Вызывает эмоцию (страх, любопытство, удивление)
        - Заставляет остаться и смотреть дальше
        """
        prompt = f"""Проанализируй заголовки и описания топовых видео и выяви ПАТТЕРНЫ КРЮЧКОВ (hooks).

ЗАГОЛОВКИ:
{chr(10).join(f'- {t}' for t in video_titles[:15])}

ОПИСАНИЯ (начало):
{chr(10).join(f'---{chr(10)}{d[:300]}' for d in video_descriptions[:10])}

=== ЗАДАЧА ===

1. Выяви какие ТИПЫ КРЮЧКОВ используются:
   - Шокирующий факт
   - Риторический вопрос
   - Противоречие/парадокс
   - Личная история
   - Обещание секрета
   - Срочность/эксклюзив

2. Создай 5 ШАБЛОНОВ мощных крючков для этой ниши

3. Для каждого шаблона дай пример

ВАЖНО: Крючок должен быть БЕЗ приветствий, сразу в тему!

Ответь в JSON:
{{
    "hook_types_used": ["тип1", "тип2"],
    "analysis": "что делает крючки этого канала эффективными",
    "templates": [
        {{
            "type": "тип крючка",
            "template": "шаблон с [ПЕРЕМЕННЫМИ]",
            "example": "конкретный пример",
            "why_works": "почему работает"
        }}
    ],
    "best_practices": ["практика 1", "практика 2"],
    "avoid": ["чего избегать"]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по YouTube retention и психологии внимания. Создаёшь крючки с 80%+ удержанием первых 30 секунд."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"raw_analysis": response}
    
    def generate_hook(self, topic: str, hook_templates: List[Dict], style: str) -> str:
        """
        Генерация мощного крючка для конкретной темы
        
        Args:
            topic: Тема видео
            hook_templates: Шаблоны крючков из analyze_hooks()
            style: Стиль канала
        
        Returns:
            Готовый текст крючка (первые 30-45 секунд видео)
        """
        templates_str = ""
        for t in hook_templates[:3]:
            templates_str += f"- {t.get('type', '')}: {t.get('template', '')}\n"
        
        prompt = f"""Создай МОЩНЫЙ крючок для YouTube видео.

ТЕМА: {topic}
СТИЛЬ: {style}

ШАБЛОНЫ КРЮЧКОВ (используй как вдохновение):
{templates_str}

=== ТРЕБОВАНИЯ ===

1. НИКАКИХ приветствий ("Привет", "Добро пожаловать", "В этом видео")
2. Сразу ИНТРИГА или ШОКИРУЮЩИЙ ФАКТ
3. Длина: 3-5 предложений (30-45 секунд озвучки)
4. Должен вызвать ЭМОЦИЮ (страх, любопытство, удивление)
5. Заканчивается интригой что будет дальше

НАПИШИ ТОЛЬКО ТЕКСТ КРЮЧКА, без пояснений."""

        response = self._chat([
            {"role": "system", "content": f"Ты сценарист YouTube с retention 80%+. Стиль: {style}. Пишешь крючки которые невозможно пропустить."},
            {"role": "user", "content": prompt}
        ], temperature=0.8, max_tokens=500)
        
        return response.strip()
    
    def generate_viral_thumbnail_concepts(self, topic: str, title: str, 
                                           script_summary: str, style: str) -> Dict[str, Any]:
        """
        Генерация 3 ВИРУСНЫХ концепций для YouTube превью
        
        Анализирует тему и создаёт 3 уникальных концепции с разными
        психологическими триггерами для максимального CTR.
        
        Returns:
            {
                "analysis": "анализ темы",
                "concepts": [
                    {
                        "type": "тип концепции",
                        "prompt_en": "детальный промпт на английском",
                        "why_viral": "почему это привлечёт внимание",
                        "psychological_trigger": "какой триггер используется"
                    }
                ]
            }
        """
        prompt = f"""Создай 3 ВИРУСНЫХ концепции для YouTube превью.

ТЕМА ВИДЕО: {topic}
ЗАГОЛОВОК: {title}
СТИЛЬ КАНАЛА: {style}

КРАТКОЕ СОДЕРЖАНИЕ:
{script_summary[:1500]}

=== ЗАДАЧА ===

Создай 3 РАЗНЫХ концепции превью, каждая с уникальным психологическим триггером:

1. **ДРАМАТИЧНАЯ** — вызывает сильные эмоции (страх, удивление, восхищение)
2. **ИНТРИГУЮЩАЯ** — вызывает любопытство, желание узнать больше
3. **ЭМОЦИОНАЛЬНАЯ** — человеческая история, лицо с эмоцией

=== ТРЕБОВАНИЯ К ПРОМПТАМ ===

Каждый промпт должен быть:
- На АНГЛИЙСКОМ языке
- ДЕТАЛЬНЫМ (минимум 50 слов)
- Описывать КОНКРЕТНУЮ сцену/композицию
- Включать: освещение, цвета, настроение, детали
- Оптимизирован для AI генератора (FLUX/Stable Diffusion)

=== ПСИХОЛОГИЧЕСКИЕ ТРИГГЕРЫ ДЛЯ CTR ===

- Контраст (свет/тьма, добро/зло)
- Эмоциональные лица (удивление, страх, решимость)
- Загадка (что-то скрытое, недосказанное)
- Масштаб (эпичность, грандиозность)
- Опасность (угроза, напряжение)
- Человечность (глаза, эмоции, история)

Ответь в JSON:
{{
    "analysis": "краткий анализ что сработает для этой темы",
    "target_emotion": "какую эмоцию должно вызывать превью",
    "concepts": [
        {{
            "type": "dramatic",
            "prompt_en": "detailed English prompt for AI image generation, describing exact scene, lighting, composition, mood, colors, style...",
            "why_viral": "почему это привлечёт клики",
            "psychological_trigger": "какой триггер используется",
            "composition": "описание композиции"
        }},
        {{
            "type": "intriguing",
            "prompt_en": "...",
            "why_viral": "...",
            "psychological_trigger": "...",
            "composition": "..."
        }},
        {{
            "type": "emotional",
            "prompt_en": "...",
            "why_viral": "...",
            "psychological_trigger": "...",
            "composition": "..."
        }}
    ]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по YouTube превью с CTR 20%+. Создаёшь превью на которые НЕВОЗМОЖНО не кликнуть. Знаешь психологию внимания и визуального маркетинга. Пишешь промпты для AI генераторов изображений. Отвечай только валидным JSON."},
            {"role": "user", "content": prompt}
        ], temperature=0.8, max_tokens=3000)
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {"concepts": [], "error": "Failed to parse response"}
    
    def analyze_competitor_thumbnail_style(self, channel_name: str, 
                                            video_titles: List[str]) -> Dict[str, Any]:
        """
        Анализ стиля превью конкурента для генерации похожих
        """
        prompt = f"""Проанализируй стиль превью (thumbnails) YouTube канала.

КАНАЛ: {channel_name}

ЗАГОЛОВКИ ВИДЕО:
{chr(10).join(f'- {t}' for t in video_titles[:15])}

На основе тематики определи типичный стиль превью для такого контента:

1. Цветовая схема (какие цвета доминируют)
2. Композиция (что обычно в центре)
3. Настроение (драматичное, яркое, мрачное)
4. Типичные элементы (лица, объекты, текст)
5. Стиль текста на превью

Ответь в JSON:
{{
    "colors": "описание цветовой схемы",
    "composition": "описание композиции",
    "mood": "настроение",
    "typical_elements": ["элемент1", "элемент2"],
    "text_style": "стиль текста",
    "prompt_style": "стиль для AI генератора (на английском)",
    "recommendations": ["рекомендация 1", "рекомендация 2"]
}}"""

        response = self._chat([
            {"role": "system", "content": "Ты эксперт по YouTube превью с CTR 15%+. Анализируешь успешные каналы."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {
                "colors": "тёмные с яркими акцентами",
                "composition": "центральный объект/лицо",
                "mood": "драматичное",
                "prompt_style": "dramatic, cinematic, high contrast, vibrant colors"
            }
