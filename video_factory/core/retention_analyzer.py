"""
Анализ retention и структуры видео конкурентов
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class RetentionPoint:
    """Точка удержания"""
    timestamp: str
    seconds: int
    event: str
    impact: str  # positive, negative, neutral


@dataclass
class VideoStructure:
    """Структура видео"""
    intro_hook: str
    chapters: List[Dict]
    hooks: List[str]
    cta_points: List[str]
    estimated_retention_curve: List[int]


class RetentionAnalyzer:
    """Анализатор retention и структуры видео"""
    
    # Паттерны хуков, которые удерживают зрителя
    HOOK_PATTERNS = [
        r"но это ещё не всё",
        r"подождите",
        r"самое интересное",
        r"вы не поверите",
        r"а теперь",
        r"но главное",
        r"секрет в том",
        r"мало кто знает",
        r"на самом деле",
        r"но есть одно но",
        r"досмотрите до конца",
        r"через минуту",
        r"сейчас покажу"
    ]
    
    # Паттерны CTA
    CTA_PATTERNS = [
        r"подпис",
        r"лайк",
        r"коммент",
        r"колокольчик",
        r"поддержать",
        r"ссылк"
    ]
    
    def __init__(self):
        pass
    
    def analyze_script_structure(self, script: str) -> VideoStructure:
        """Анализ структуры сценария"""
        
        lines = script.split('\n')
        
        # Ищем главы
        chapters = []
        chapter_pattern = r'\[(?:ГЛАВА|CHAPTER|INTRO|OUTRO|HOOK).*?\]'
        
        for i, line in enumerate(lines):
            match = re.search(chapter_pattern, line, re.IGNORECASE)
            if match:
                chapters.append({
                    'title': match.group(),
                    'line_number': i,
                    'content_preview': lines[i+1][:100] if i+1 < len(lines) else ""
                })
        
        # Ищем хуки
        hooks = []
        for pattern in self.HOOK_PATTERNS:
            matches = re.findall(pattern, script, re.IGNORECASE)
            hooks.extend(matches)
        
        # Ищем CTA
        cta_points = []
        for pattern in self.CTA_PATTERNS:
            if re.search(pattern, script, re.IGNORECASE):
                cta_points.append(pattern)
        
        # Извлекаем intro hook (первые 100 слов)
        words = script.split()[:100]
        intro_hook = ' '.join(words)
        
        # Оценка кривой retention (упрощённая)
        retention_curve = self._estimate_retention_curve(script, chapters, hooks)
        
        return VideoStructure(
            intro_hook=intro_hook,
            chapters=chapters,
            hooks=list(set(hooks)),
            cta_points=list(set(cta_points)),
            estimated_retention_curve=retention_curve
        )
    
    def _estimate_retention_curve(
        self, 
        script: str, 
        chapters: List[Dict], 
        hooks: List[str]
    ) -> List[int]:
        """Оценка кривой retention"""
        
        # Базовая кривая (типичное падение)
        # 100% -> постепенное снижение
        base_curve = [100, 85, 75, 68, 62, 58, 55, 52, 50, 48, 45]
        
        # Корректируем на основе хуков
        hook_bonus = min(len(hooks) * 2, 15)  # До +15%
        
        # Корректируем на основе глав (структурированность)
        chapter_bonus = min(len(chapters) * 3, 10)  # До +10%
        
        # Применяем бонусы
        adjusted_curve = []
        for i, val in enumerate(base_curve):
            adjusted = val + hook_bonus + chapter_bonus
            # Не больше 100%
            adjusted_curve.append(min(adjusted, 100))
        
        return adjusted_curve
    
    def get_retention_tips(self, structure: VideoStructure) -> List[str]:
        """Советы по улучшению retention"""
        
        tips = []
        
        # Проверяем intro
        if len(structure.intro_hook.split()) < 50:
            tips.append("⚠️ Intro слишком короткий. Добавьте интригу в первые 30 секунд.")
        
        # Проверяем хуки
        if len(structure.hooks) < 3:
            tips.append("⚠️ Мало хуков. Добавьте фразы типа 'но это ещё не всё', 'самое интересное впереди'.")
        else:
            tips.append(f"✓ Хорошо! Найдено {len(structure.hooks)} хуков для удержания.")
        
        # Проверяем главы
        if len(structure.chapters) < 3:
            tips.append("⚠️ Добавьте больше глав для лучшей структуры.")
        else:
            tips.append(f"✓ Отличная структура: {len(structure.chapters)} глав.")
        
        # Проверяем CTA
        if len(structure.cta_points) == 0:
            tips.append("⚠️ Нет призывов к действию. Добавьте просьбу подписаться/лайкнуть.")
        
        # Общие советы
        tips.extend([
            "💡 Добавляйте визуальные хуки каждые 30-60 секунд",
            "💡 Используйте открытые петли (начните историю, закончите позже)",
            "💡 Меняйте темп повествования для удержания внимания"
        ])
        
        return tips
    
    def analyze_competitor_titles(self, titles: List[str]) -> Dict[str, Any]:
        """Анализ заголовков конкурентов на retention-паттерны"""
        
        patterns_found = {
            "numbers": 0,      # "5 причин", "ТОП 10"
            "questions": 0,    # "Почему?", "Как?"
            "intrigue": 0,     # "Секрет", "Правда о"
            "urgency": 0,      # "Срочно", "Наконец-то"
            "negative": 0,     # "Ошибки", "Провал"
            "positive": 0,     # "Лучший", "Идеальный"
        }
        
        for title in titles:
            title_lower = title.lower()
            
            # Числа
            if re.search(r'\d+', title):
                patterns_found["numbers"] += 1
            
            # Вопросы
            if '?' in title or any(w in title_lower for w in ['почему', 'как', 'что', 'зачем', 'why', 'how', 'what']):
                patterns_found["questions"] += 1
            
            # Интрига
            if any(w in title_lower for w in ['секрет', 'правда', 'скрыв', 'тайн', 'secret', 'truth', 'hidden']):
                patterns_found["intrigue"] += 1
            
            # Срочность
            if any(w in title_lower for w in ['срочно', 'наконец', 'впервые', 'шок', 'urgent', 'finally', 'breaking']):
                patterns_found["urgency"] += 1
            
            # Негатив
            if any(w in title_lower for w in ['ошибк', 'провал', 'худш', 'никогда', 'mistake', 'fail', 'worst']):
                patterns_found["negative"] += 1
            
            # Позитив
            if any(w in title_lower for w in ['лучш', 'идеальн', 'топ', 'best', 'perfect', 'amazing']):
                patterns_found["positive"] += 1
        
        total = len(titles)
        percentages = {k: round(v / total * 100, 1) for k, v in patterns_found.items()}
        
        # Определяем доминирующий паттерн
        dominant = max(patterns_found, key=patterns_found.get)
        
        return {
            "patterns": patterns_found,
            "percentages": percentages,
            "dominant_pattern": dominant,
            "recommendation": self._get_title_recommendation(dominant, percentages)
        }
    
    def _get_title_recommendation(self, dominant: str, percentages: Dict) -> str:
        """Рекомендация по заголовкам"""
        
        recommendations = {
            "numbers": "Используйте числа в заголовках (ТОП 5, 10 фактов)",
            "questions": "Задавайте вопросы, на которые зритель хочет узнать ответ",
            "intrigue": "Создавайте интригу, обещайте раскрыть секреты",
            "urgency": "Добавляйте элемент срочности и эксклюзивности",
            "negative": "Негативные заголовки привлекают внимание (ошибки, провалы)",
            "positive": "Позитивные заголовки работают для обучающего контента"
        }
        
        return recommendations.get(dominant, "Экспериментируйте с разными форматами заголовков")
