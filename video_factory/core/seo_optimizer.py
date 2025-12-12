"""
SEO оптимизация для YouTube
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import re


@dataclass
class SEOResult:
    """Результат SEO оптимизации"""
    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    score: int
    recommendations: List[str]


class SEOOptimizer:
    """Оптимизатор SEO для YouTube"""
    
    # Максимальные длины
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS = 500  # символов
    OPTIMAL_TAGS_COUNT = 30
    
    def __init__(self):
        pass
    
    def optimize_title(self, title: str, keywords: List[str] = None) -> Dict[str, Any]:
        """Оптимизация заголовка"""
        
        score = 0
        recommendations = []
        
        # Длина
        if len(title) <= self.MAX_TITLE_LENGTH:
            score += 20
        else:
            recommendations.append(f"Сократите заголовок до {self.MAX_TITLE_LENGTH} символов")
        
        # Оптимальная длина 50-70
        if 50 <= len(title) <= 70:
            score += 15
        elif len(title) < 50:
            recommendations.append("Заголовок слишком короткий (оптимально 50-70 символов)")
        
        # Ключевые слова в начале
        if keywords:
            title_lower = title.lower()
            for kw in keywords[:3]:
                if kw.lower() in title_lower[:30]:
                    score += 10
                    break
            else:
                recommendations.append("Добавьте ключевое слово в начало заголовка")
        
        # Числа
        if re.search(r'\d+', title):
            score += 10
        else:
            recommendations.append("Добавьте число для привлечения внимания (ТОП 5, 10 фактов)")
        
        # Эмоциональные слова
        emotional_words = ['шок', 'невероятн', 'удивительн', 'секрет', 'правда', 'лучш', 'худш']
        if any(w in title.lower() for w in emotional_words):
            score += 10
        
        # Без кликбейта (caps lock)
        if title.isupper():
            score -= 10
            recommendations.append("Избегайте CAPS LOCK — это выглядит как спам")
        
        return {
            "title": title,
            "length": len(title),
            "score": min(score, 100),
            "recommendations": recommendations
        }
    
    def generate_description(
        self,
        title: str,
        script_summary: str,
        keywords: List[str],
        chapters: List[Dict] = None,
        links: Dict[str, str] = None
    ) -> str:
        """Генерация оптимизированного описания"""
        
        description_parts = []
        
        # Первые 150 символов — самые важные (показываются в поиске)
        hook = f"{title}\n\n{script_summary[:200]}..."
        description_parts.append(hook)
        
        # Ключевые слова (естественно вписанные)
        if keywords:
            kw_text = f"\n\nВ этом видео: {', '.join(keywords[:10])}"
            description_parts.append(kw_text)
        
        # Таймкоды (главы)
        if chapters:
            description_parts.append("\n\n⏱ ТАЙМКОДЫ:")
            for ch in chapters:
                timecode = ch.get('timecode', '0:00')
                name = ch.get('name', ch.get('title', 'Глава'))
                description_parts.append(f"{timecode} - {name}")
        
        # Призыв к действию
        cta = """
        
🔔 Подпишись на канал и включи уведомления!
👍 Поставь лайк, если видео было полезным
💬 Напиши в комментариях, что думаешь
"""
        description_parts.append(cta)
        
        # Ссылки
        if links:
            description_parts.append("\n📎 ССЫЛКИ:")
            for name, url in links.items():
                description_parts.append(f"• {name}: {url}")
        
        # Ключевые слова в конце (для SEO)
        if keywords:
            description_parts.append(f"\n\n#{' #'.join(keywords[:5])}")
        
        return '\n'.join(description_parts)
    
    def generate_tags(
        self,
        title: str,
        keywords: List[str],
        competitor_tags: List[str] = None,
        niche: str = ""
    ) -> List[str]:
        """Генерация тегов"""
        
        tags = []
        
        # Основные ключевые слова
        tags.extend(keywords[:15])
        
        # Из заголовка
        title_words = re.findall(r'\b\w{4,}\b', title.lower())
        tags.extend(title_words[:5])
        
        # Теги конкурентов (если есть)
        if competitor_tags:
            # Берём популярные теги конкурентов
            tags.extend(competitor_tags[:10])
        
        # Ниша
        if niche:
            tags.append(niche)
            tags.append(f"{niche} видео")
            tags.append(f"{niche} на русском")
        
        # Общие теги
        general_tags = [
            "интересные факты",
            "познавательное видео",
            "документальный фильм",
            "история",
            "топ"
        ]
        tags.extend(general_tags[:3])
        
        # Убираем дубликаты и пустые
        tags = list(dict.fromkeys([t.strip() for t in tags if t.strip()]))
        
        # Ограничиваем количество
        return tags[:self.OPTIMAL_TAGS_COUNT]
    
    def generate_hashtags(self, keywords: List[str], niche: str = "") -> List[str]:
        """Генерация хештегов (максимум 3 в заголовке, 15 в описании)"""
        
        hashtags = []
        
        # Основные
        for kw in keywords[:3]:
            # Убираем пробелы для хештега
            hashtag = "#" + kw.replace(" ", "").replace("-", "")
            hashtags.append(hashtag)
        
        # Ниша
        if niche:
            hashtags.append("#" + niche.replace(" ", ""))
        
        # Общие популярные
        hashtags.extend(["#shorts", "#факты", "#интересно"])
        
        return hashtags[:15]
    
    def analyze_seo(
        self,
        title: str,
        description: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """Полный анализ SEO"""
        
        score = 0
        issues = []
        good_points = []
        
        # Заголовок
        if len(title) <= 100:
            score += 15
            good_points.append("✓ Заголовок оптимальной длины")
        else:
            issues.append("✗ Заголовок слишком длинный")
        
        if re.search(r'\d+', title):
            score += 10
            good_points.append("✓ Заголовок содержит число")
        
        # Описание
        if len(description) >= 200:
            score += 15
            good_points.append("✓ Описание достаточно подробное")
        else:
            issues.append("✗ Описание слишком короткое")
        
        if "http" in description or "https" in description:
            score += 5
            good_points.append("✓ Есть ссылки в описании")
        
        # Таймкоды
        if re.search(r'\d{1,2}:\d{2}', description):
            score += 15
            good_points.append("✓ Есть таймкоды (главы)")
        else:
            issues.append("✗ Добавьте таймкоды для навигации")
        
        # Теги
        if len(tags) >= 10:
            score += 15
            good_points.append(f"✓ Достаточно тегов ({len(tags)})")
        else:
            issues.append(f"✗ Мало тегов ({len(tags)}, рекомендуется 20-30)")
        
        # Хештеги
        hashtag_count = description.count('#')
        if 1 <= hashtag_count <= 15:
            score += 10
            good_points.append("✓ Оптимальное количество хештегов")
        elif hashtag_count > 15:
            issues.append("✗ Слишком много хештегов (максимум 15)")
        
        # CTA
        cta_words = ['подпис', 'лайк', 'коммент', 'колокольчик']
        if any(w in description.lower() for w in cta_words):
            score += 10
            good_points.append("✓ Есть призыв к действию")
        else:
            issues.append("✗ Добавьте призыв подписаться/лайкнуть")
        
        return {
            "score": min(score, 100),
            "grade": self._get_grade(score),
            "good_points": good_points,
            "issues": issues,
            "title_length": len(title),
            "description_length": len(description),
            "tags_count": len(tags)
        }
    
    def _get_grade(self, score: int) -> str:
        """Оценка SEO"""
        if score >= 80:
            return "A (Отлично)"
        elif score >= 60:
            return "B (Хорошо)"
        elif score >= 40:
            return "C (Удовлетворительно)"
        else:
            return "D (Требует улучшения)"
