"""
Клиент Groq API для генерации текста
С АВТОМАТИЧЕСКОЙ РОТАЦИЕЙ КЛЮЧЕЙ при исчерпании лимита!
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
import time
from groq import Groq


@dataclass
class AnalysisResult:
    """Результат анализа"""
    triggers: Dict[str, List[str]]
    style: Dict[str, str]
    recommendations: List[str]


class GroqClient:
    """
    Клиент для работы с Groq API
    
    Поддерживает АВТОМАТИЧЕСКУЮ РОТАЦИЮ ключей при rate limit!
    Если один ключ исчерпан — автоматически переключается на следующий.
    """
    
    def __init__(self, api_key: str = None, api_keys: List[str] = None, 
                 model: str = "llama-3.3-70b-versatile"):
        # Поддержка нескольких ключей
        if api_keys:
            self.api_keys = [k for k in api_keys if k and k.startswith("gsk_")]
        elif api_key:
            self.api_keys = [api_key] if api_key.startswith("gsk_") else []
        else:
            self.api_keys = []
        
        self._current_key_idx = 0
        self._key_cooldowns = {}  # key -> время когда можно снова использовать
        self.model = model
        
        # Создаём клиент с первым ключом
        if self.api_keys:
            self.client = Groq(api_key=self.api_keys[0])
        else:
            raise ValueError("Нет Groq API ключей!")
        
        print(f"[Groq] Инициализирован с {len(self.api_keys)} ключами")
    
    def _get_available_key(self) -> str:
        """Получение доступного ключа (не в cooldown)"""
        now = time.time()
        
        # Ищем ключ не в cooldown
        for i in range(len(self.api_keys)):
            idx = (self._current_key_idx + i) % len(self.api_keys)
            key = self.api_keys[idx]
            
            cooldown_until = self._key_cooldowns.get(key, 0)
            if now >= cooldown_until:
                if idx != self._current_key_idx:
                    self._current_key_idx = idx
                    self.client = Groq(api_key=key)
                    print(f"[Groq] Переключился на ключ #{idx+1}")
                return key
        
        # Все ключи в cooldown — ждём минимальное время
        min_wait = min(self._key_cooldowns.values()) - now
        if min_wait > 0:
            print(f"[Groq] Все ключи в cooldown. Жду {min_wait:.0f} сек...")
            time.sleep(min(min_wait + 1, 60))  # Максимум 60 сек
        
        return self._get_available_key()
    
    def _mark_key_cooldown(self, key: str, seconds: int = 60):
        """Пометить ключ как в cooldown"""
        self._key_cooldowns[key] = time.time() + seconds
        print(f"[Groq] Ключ #{self.api_keys.index(key)+1} в cooldown на {seconds}с")
    
    def _chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Базовый метод для чата с автоматической ротацией ключей"""
        max_retries = len(self.api_keys) + 1
        last_error = None
        
        for attempt in range(max_retries):
            key = self._get_available_key()
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e)
                last_error = e
                
                # Rate limit — переключаемся на другой ключ
                if "429" in error_msg or "rate_limit" in error_msg.lower():
                    # Определяем время cooldown из сообщения
                    import re
                    cooldown = 0
                    
                    if "try again in" in error_msg.lower():
                        # Парсим минуты и секунды
                        match_m = re.search(r'(\d+)m', error_msg)
                        match_s = re.search(r'(\d+(?:\.\d+)?)s', error_msg)
                        
                        if match_m:
                            cooldown += int(match_m.group(1)) * 60
                        if match_s:
                            cooldown += int(float(match_s.group(1)))
                    
                    # Если не удалось распарсить — ставим 1 час (дневной лимит)
                    if cooldown == 0:
                        cooldown = 3600
                    
                    self._mark_key_cooldown(key, cooldown)
                    continue
                
                # Другая ошибка — пробуем ещё раз
                print(f"[Groq] Ошибка: {error_msg[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        
        raise last_error or Exception("Все Groq ключи исчерпаны")
    
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
        Генерация ДЕРЗКИХ подниш с высоким вирусным потенциалом
        """
        prompt = f"""Найди 5 ДЕРЗКИХ, ПРОВОКАЦИОННЫХ подниш для YouTube канала.

ОСНОВНАЯ ТЕМА: {main_topic}
КОНКУРЕНТ: {competitor_info}

=== КРИТЕРИИ ИДЕАЛЬНОЙ ПОДНИШИ ===

🔥 ДЕРЗОСТЬ И ПРОВОКАЦИЯ (в рамках правил YouTube):
- Темы которые вызывают СИЛЬНЫЕ эмоции
- Контроверсионные но НЕ запрещённые темы
- "Запретные" истории которые мало кто рассказывает
- Шокирующие факты и разоблачения
- Тёмные стороны известных событий/людей

💀 ПРИМЕРЫ ДЕРЗКИХ УГЛОВ:
- "Секретные операции которые скрывали 50 лет"
- "Преступления которые сошли с рук"
- "Тёмная сторона [известной личности]"
- "Что на самом деле произошло в [событие]"
- "Запрещённые эксперименты [страны/организации]"
- "Предательства которые изменили историю"
- "Жестокие методы [армии/спецслужб]"

⚠️ ГРАНИЦЫ (не переходить):
- Никакого экстремизма и призывов к насилию
- Никакой пропаганды
- Факты, а не выдумки
- Исторический контекст обязателен

=== ЗАДАЧА ===

Придумай 5 ДЕРЗКИХ подниш которые:
1. Вызывают мурашки и желание узнать больше
2. Имеют "запретный" привкус но легальны
3. Мало кто делает качественно
4. Огромный вирусный потенциал

Ответь в JSON:
{{
    "subniches": [
        {{
            "name": "ДЕРЗКОЕ название подниши",
            "description": "почему это цепляет",
            "search_demand": {{
                "score": 9,
                "reasoning": "почему люди хотят это смотреть",
                "search_queries": ["примеры запросов"]
            }},
            "competition": {{
                "score": 3,
                "reasoning": "почему мало конкурентов"
            }},
            "viral_potential": {{
                "score": 10,
                "reasoning": "почему будет вирусится"
            }},
            "why_works": "почему эта дерзкая тема сработает",
            "example_topics": ["5 ДЕРЗКИХ тем для видео"],
            "target_audience": "кто будет смотреть",
            "shock_factor": "что шокирует в этой теме"
        }}
    ],
    "recommended": "самая дерзкая но безопасная подниша",
    "analysis_summary": "вывод"
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
        Генерация ДЕРЗКИХ, ЦЕПЛЯЮЩИХ тем для видео
        """
        import random
        
        # ДЕРЗКИЕ углы подачи
        angles = [
            "🔥 ШОКИРУЮЩИЕ секреты и разоблачения",
            "💀 Тёмная сторона и скрытая правда",
            "⚠️ Запрещённые факты которые скрывали",
            "🩸 Жестокая реальность без цензуры",
            "👁 Заговоры и тайные операции",
            "💣 Предательства и измены",
            "🔪 Преступления которые сошли с рук",
            "☠️ Смертельные ошибки и катастрофы"
        ]
        
        random.seed(variation_seed if variation_seed else None)
        selected_angles = random.sample(angles, min(3, len(angles)))
        
        excluded_str = ""
        if excluded_topics:
            excluded_str = f"""
НЕ ПРЕДЛАГАТЬ (уже были):
{chr(10).join(f'- {t}' for t in excluded_topics[-20:])}
"""
        
        prompt = f"""Сгенерируй {count} ДЕРЗКИХ, ПРОВОКАЦИОННЫХ тем для YouTube.

ПОДНИША: {subniche}
СТИЛЬ: {style_info}

=== ДЕРЗКИЕ УГЛЫ (используй) ===
{chr(10).join(selected_angles)}
{excluded_str}

=== ФОРМУЛЫ ДЕРЗКИХ ЗАГОЛОВКОВ ===

🔥 ШОКИРУЮЩИЕ:
- "Почему [X] на самом деле был [негатив]"
- "Тёмная правда о [известное событие]"
- "[Число] жертв [события] о которых молчат"

💀 ЗАПРЕТНЫЕ:
- "Секретные документы раскрыли [шок]"
- "Что скрывали [страна/организация] 50 лет"
- "Запрещённая правда о [тема]"

⚠️ РАЗОБЛАЧЕНИЯ:
- "Ложь о [известный факт]: что было на самом деле"
- "Как [герой] на самом деле [негатив]"
- "Преступление [личности] которое замяли"

🩸 ЖЁСТКИЕ:
- "Самая жестокая [операция/битва/казнь]"
- "Как [армия] уничтожила [число] за [время]"
- "[Метод пыток/казни] который использовали [кто]"

=== ВАЖНО ===
- Дерзко но в рамках YouTube (без бана)
- Основано на реальных фактах
- Вызывает СИЛЬНЫЕ эмоции
- Невозможно не кликнуть

Ответь в JSON:
{{
    "topics": [
        {{
            "title": "ДЕРЗКИЙ заголовок",
            "hook": "шокирующий хук для начала",
            "description": "о чём видео",
            "angle": "какой дерзкий угол",
            "viral_potential": 9,
            "why_works": "почему это взорвёт",
            "shock_factor": "что шокирует",
            "target_emotion": "страх/ужас/любопытство/гнев"
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
    
    def generate_script(self, topic: str, duration: str, style: str, 
                        language: str = "Русский", include_hooks: bool = True) -> str:
        """
        Генерация сценария по главам
        
        40-50 минут = ~45000 СИМВОЛОВ (не слов!)
        ~1000 символов = 1 минута озвучки
        Разбиваем на 12-15 глав для удобства генерации
        """
        # СИМВОЛЫ (не слова!) для каждой длительности
        # ElevenLabs озвучивает ~1200 символов = 1 минута (быстрее чем ожидалось)
        # Поэтому добавляем +20% к символам для компенсации
        duration_map = {
            "10-20 минут": (18000, 15, 5),     # 18K символов (+20%), 15 мин, 5 глав
            "20-30 минут": (30000, 25, 8),     # 30K символов (+20%), 25 мин, 8 глав
            "30-40 минут": (42000, 35, 10),    # 42K символов (+20%), 35 мин, 10 глав
            "40-50 минут": (54000, 45, 12),    # 54K символов (+20%), 45 мин, 12 глав
            "50-60 минут": (66000, 55, 14),    # 66K символов (+20%), 55 мин, 14 глав
            "60+ минут": (78000, 65, 16)       # 78K символов (+20%), 65 мин, 16 глав
        }
        
        target_chars, mins, num_chapters = duration_map.get(duration, (45000, 45, 12))
        chars_per_chapter = target_chars // num_chapters  # ~3000-4000 символов на главу
        
        # Определяем язык
        is_english = language.lower() in ["english", "английский", "en"]
        
        # Генерируем сценарий по главам
        full_script = self._generate_script_by_chapters(
            topic=topic,
            style=style,
            target_chars=target_chars,
            num_chapters=num_chapters,
            chars_per_chapter=chars_per_chapter,
            mins=mins,
            is_english=is_english
        )
        
        return full_script
    
    def _generate_script_by_chapters(self, topic: str, style: str, 
                                       target_chars: int, num_chapters: int,
                                       chars_per_chapter: int, mins: int, 
                                       is_english: bool) -> str:
        """
        Генерация сценария по главам
        
        Каждая глава ~3000-4000 символов для удобства генерации
        """
        print(f"[Groq] Генерация сценария: {target_chars} символов, {num_chapters} глав")
        
        # Генерируем план глав
        chapters = self._generate_chapter_plan(topic, num_chapters, is_english)
        
        print(f"[Groq] План: {len(chapters)} глав по ~{chars_per_chapter} символов")
        
        # Генерируем каждую главу
        full_script_parts = []
        
        # HOOK (короткий, ~500 символов)
        hook = self._generate_single_chapter(
            topic=topic,
            chapter_title="HOOK" if is_english else "КРЮЧОК", 
            chapter_num=0,
            total_chapters=len(chapters),
            target_chars=500,
            style=style,
            is_english=is_english,
            context=""
        )
        full_script_parts.append(f"[HOOK]\n\n{hook}")
        
        # Основные главы
        context = hook[-300:]
        
        for i, chapter_title in enumerate(chapters):
            print(f"  Глава {i+1}/{len(chapters)}: {chapter_title[:30]}...")
            
            chapter_text = self._generate_single_chapter(
                topic=topic,
                chapter_title=chapter_title,
                chapter_num=i+1,
                total_chapters=len(chapters),
                target_chars=chars_per_chapter,
                style=style,
                is_english=is_english,
                context=context
            )
            
            marker = f"CHAPTER {i+1}" if is_english else f"ГЛАВА {i+1}"
            full_script_parts.append(f"[{marker}: {chapter_title}]\n\n{chapter_text}")
            context = chapter_text[-300:]
        
        # CONCLUSION (~500 символов)
        conclusion = self._generate_single_chapter(
            topic=topic,
            chapter_title="CONCLUSION" if is_english else "ЗАКЛЮЧЕНИЕ",
            chapter_num=len(chapters)+1,
            total_chapters=len(chapters),
            target_chars=500,
            style=style,
            is_english=is_english,
            context=context
        )
        full_script_parts.append(f"[{'CONCLUSION' if is_english else 'ЗАКЛЮЧЕНИЕ'}]\n\n{conclusion}")
        
        full_script = "\n\n".join(full_script_parts)
        
        actual_chars = len(full_script)
        actual_mins = actual_chars / 1000  # ~1000 символов = 1 минута
        print(f"[Groq] ✅ Сценарий: {actual_chars} символов (~{actual_mins:.0f} мин)")
        
        return full_script
    
    def _generate_chapter_plan(self, topic: str, num_chapters: int, is_english: bool) -> list:
        """Генерация плана глав"""
        if is_english:
            prompt = f"""Create {num_chapters} chapter titles for a documentary.

Topic: {topic}
(If topic is in Russian, translate it and create English titles about that topic)

!!! WRITE ONLY IN ENGLISH !!!
DO NOT USE RUSSIAN OR CYRILLIC!

Reply with ONLY chapter titles in English, one per line:
1. [English title]
2. [English title]
..."""
            system_msg = "You write ONLY in English. Never use Russian or Cyrillic characters. Create chapter titles in English."
        else:
            prompt = f"""Создай {num_chapters} названий глав для документального видео о: {topic}

Ответь ТОЛЬКО названиями, по одному на строку:
1. [название]
2. [название]
..."""
            system_msg = "Создай названия глав."
        
        response = self._chat([
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ], temperature=0.7, max_tokens=500)
        
        # Парсим
        chapters = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and len(line) > 3:
                # Убираем номер в начале
                import re
                clean = re.sub(r'^[\d\.\)\-\:]+\s*', '', line).strip()
                if clean:
                    chapters.append(clean)
        
        # Если мало — добавляем дефолтные
        while len(chapters) < num_chapters:
            chapters.append(f"Part {len(chapters)+1}" if is_english else f"Часть {len(chapters)+1}")
        
        return chapters[:num_chapters]
    
    def _generate_single_chapter(self, topic: str, chapter_title: str, 
                                  chapter_num: int, total_chapters: int,
                                  target_chars: int, style: str,
                                  is_english: bool, context: str) -> str:
        """Генерация одной главы (~3500-4500 символов)"""
        
        # Рассчитываем max_tokens: ~4 символа на токен + запас
        max_tokens = max(3000, (target_chars // 3) + 500)
        
        if is_english:
            # Переводим тему на английский если она на русском
            topic_instruction = f"""Topic: {topic}
NOTE: If the topic above is in Russian, translate it to English and write about that topic."""
            
            prompt = f"""Write chapter "{chapter_title}" for a documentary.

{topic_instruction}

!!! CRITICAL LANGUAGE REQUIREMENT !!!
YOU MUST WRITE ONLY IN ENGLISH!
DO NOT WRITE IN RUSSIAN!
DO NOT USE CYRILLIC CHARACTERS!
EVERY SINGLE WORD MUST BE IN ENGLISH!

Target length: {target_chars} characters. This is chapter {chapter_num} of {total_chapters}.

Previous context: {context[:200]}...

REQUIREMENTS:
- Write MINIMUM {target_chars} characters IN ENGLISH ONLY
- Include specific facts, dates, names, numbers
- Detailed narrative with historical accuracy
- Natural voiceover text (no stage directions)
- NO greetings, start directly with content
- Write ALL dates in WORDS: "nineteen forty-four" NOT "1944"

Write the full chapter now IN ENGLISH (minimum {target_chars} characters):"""
            system_msg = f"You are an English documentary scriptwriter. Style: {style}. CRITICAL: You MUST write ONLY in English. Never use Russian or Cyrillic. Write at least {target_chars} characters."
        else:
            prompt = f"""Напиши главу "{chapter_title}" для документального видео о: {topic}

КРИТИЧЕСКИ ВАЖНО: Напиши РОВНО {target_chars} символов (не слов!). Это глава {chapter_num} из {total_chapters}.

Предыдущий контекст: {context[:200]}...

ТРЕБОВАНИЯ:
- Напиши МИНИМУМ {target_chars} символов текста
- Включи конкретные факты, даты, имена, числа
- Детальное повествование с исторической точностью
- Естественный текст для озвучки (без ремарок)
- БЕЗ приветствий, сразу в тему
- Продолжай писать пока не достигнешь {target_chars} символов
- ВАЖНО: Пиши ВСЕ даты ПРОПИСЬЮ! Пример: "тысяча девятьсот сорок четвёртый год" НЕ "1944", "пятнадцатое октября" НЕ "15 октября"
- Это помогает AI озвучке правильно произносить даты

Напиши полную главу (минимум {target_chars} символов):"""
            system_msg = f"Сценарист документальных видео. Стиль: {style}. Ты ОБЯЗАН написать минимум {target_chars} символов. Будь детальным и подробным. ВСЕГДА пиши даты прописью!"
        
        response = self._chat([
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ], temperature=0.8, max_tokens=max_tokens)
        
        return response.strip()
    
    # Оставляем старую функцию для совместимости
    def _generate_chapter(self, topic: str, chapter_title: str, chapter_num: int,
                          total_chapters: int, words_target: int, style: str,
                          is_english: bool, previous_summary: str) -> str:
        """Старая функция — перенаправляем на новую"""
        return self._generate_single_chapter(
            topic=topic,
            chapter_title=chapter_title,
            chapter_num=chapter_num,
            total_chapters=total_chapters,
            target_chars=words_target * 6,  # ~6 символов на слово
            style=style,
            is_english=is_english,
            context=previous_summary
        )
    
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
                     subniche: str = "", channel_keywords: List[str] = None,
                     language: str = "Русский") -> Dict[str, Any]:
        """
        Генерация SEO: описание, теги, хештеги
        С поддержкой языка!
        """
        keywords_str = ', '.join(channel_keywords[:20]) if channel_keywords else ''
        is_english = language.lower() in ["english", "английский", "en"]
        
        if is_english:
            prompt = f"""Create PROFESSIONAL SEO optimization for a YouTube video.

TITLE: {title}

CHANNEL SUBNICHE: {subniche}

SCRIPT (beginning):
{script[:3000]}

COMPETITOR TAGS:
{', '.join(competitor_tags[:30])}

CHANNEL KEYWORDS:
{keywords_str}

=== TASKS ===

1. DESCRIPTION (2000-3000 characters):
   - First 150 characters are most important (visible in search)
   - Keywords in first 2-3 sentences
   - Timestamps for navigation
   - Call to action (subscribe, like)
   - Social media links (placeholders)

2. TAGS (30 tags, STRATEGY):
   - 5 high-volume (100K+ searches) — for reach
   - 10 medium-volume (10K-100K) — balance
   - 10 low-volume (1K-10K) — precise targeting
   - 5 long-tail phrases — conversion

3. HASHTAGS (5):
   - Only popular with high reach
   - Relevant to video topic
   - Mix of general and niche

4. ALTERNATIVE TITLES (3):
   - Different triggers (question, number, intrigue)
   - A/B test variants

Reply in JSON:
{{
    "description": "full description with timestamps and calls to action",
    "tags": ["tag1", "tag2", ...],
    "tags_strategy": {{
        "high_volume": ["high volume tags"],
        "medium_volume": ["medium"],
        "low_volume": ["low but precise"],
        "long_tail": ["long phrases"]
    }},
    "hashtags": ["#hashtag1", ...],
    "seo_title_alternatives": ["variant1", "variant2", "variant3"],
    "first_comment": "text for pinned comment"
}}"""
            system_msg = "You are a YouTube SEO specialist with experience promoting million-subscriber channels. Reply only with valid JSON. Write in English."
        else:
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
            system_msg = "Ты SEO специалист YouTube с опытом продвижения каналов-миллионников. Отвечай только валидным JSON."

        response = self._chat([
            {"role": "system", "content": system_msg},
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
        # 45000 слов для 40-50 минут как просил пользователь
        duration_map = {
            "10-20 минут": (15000, 15),
            "20-30 минут": (25000, 25),
            "30-40 минут": (35000, 35),
            "40-50 минут": (45000, 45),
            "50-60 минут": (55000, 55),
            "60+ минут": (65000, 65)
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
        Генерация ДЕРЗКИХ подниш (исключая отклонённые)
        """
        prompt = f"""Предложи 5 ДЕРЗКИХ, ПРОВОКАЦИОННЫХ подниш для YouTube.

ОСНОВНАЯ НИША: {main_niche}

ОТКЛОНЁННЫЕ (НЕ ПРЕДЛАГАТЬ):
{chr(10).join(f'- {r}' for r in rejected)}

КОНТЕКСТ: {style_context}

=== НУЖНЫ ДЕРЗКИЕ ПОДНИШИ ===

Примеры ДЕРЗКИХ направлений:
- "Секретные операции [спецслужб]"
- "Преступления [армий/режимов] которые скрывали"
- "Тёмная сторона [известных личностей]"
- "Запрещённые эксперименты над людьми"
- "Предательства которые изменили историю"
- "Массовые убийства о которых молчат"
- "Заговоры которые оказались правдой"
- "Жестокие методы [допросов/пыток/казней]"

⚠️ В рамках YouTube (без бана), но ДЕРЗКО!

Ответь в JSON:
{{
    "subniches": [
        {{
            "name": "ДЕРЗКОЕ название",
            "description": "почему это цепляет",
            "search_demand": {{"score": 9, "reasoning": "почему ищут"}},
            "competition": {{"score": 3, "reasoning": "почему мало конкурентов"}},
            "viral_potential": {{"score": 10, "reasoning": "почему вирусится"}},
            "why_works": "почему сработает",
            "example_topics": ["дерзкая тема 1", "дерзкая тема 2", "дерзкая тема 3"],
            "shock_factor": "что шокирует"
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
        # Определяем военную тематику для Ч/Б стиля
        topic_lower = topic.lower() if topic else ""
        is_war_theme = any(w in topic_lower for w in ['война', 'военн', 'ww2', 'wwii', 'битва', 'сражен', 'war', 'battle', 'military', 'soldier', 'army'])
        
        style_instruction = ""
        if is_war_theme:
            style_instruction = """
=== ВАЖНО: СТИЛЬ ДЛЯ ВОЕННОЙ ТЕМАТИКИ ===
Все промпты ОБЯЗАТЕЛЬНО должны включать:
- "black and white photograph" — Ч/Б стиль как у топовых военных каналов
- "vintage 1940s documentary style" — аутентичность эпохи
- "high contrast monochrome" — драматичность
- "grainy film texture" — текстура плёнки
Это стиль который работает у конкурентов с миллионами просмотров!
"""
        
        prompt = f"""Создай 3 ВИРУСНЫХ концепции для YouTube превью.
{style_instruction}

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


# === ГЛОБАЛЬНЫЙ КЛИЕНТ С РОТАЦИЕЙ ===

_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """
    Получение глобального GroqClient с автоматической ротацией ключей
    
    Использование:
        from core.groq_client import get_groq_client
        groq = get_groq_client()
        result = groq.chat("Привет!")
    """
    global _groq_client
    
    if _groq_client is None:
        from config import config
        
        # Используем все ключи для ротации
        keys = config.api.groq_keys if config.api.groq_keys else [config.api.groq_key]
        keys = [k for k in keys if k]  # Убираем пустые
        
        if not keys:
            raise ValueError("Нет Groq API ключей! Добавьте GROQ_API_KEYS в .env")
        
        _groq_client = GroqClient(
            api_keys=keys,
            model=config.api.groq_model
        )
    
    return _groq_client


def reset_groq_client():
    """Сброс клиента (для перезагрузки ключей)"""
    global _groq_client
    _groq_client = None
