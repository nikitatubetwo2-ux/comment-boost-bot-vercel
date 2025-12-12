"""
Контроль качества — проверка проекта перед рендером
"""

from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class QualityIssue:
    """Проблема качества"""
    severity: str  # critical, warning, info
    category: str  # images, audio, script, sync
    message: str
    fix_suggestion: str


@dataclass
class QualityReport:
    """Отчёт о качестве"""
    passed: bool
    score: int  # 0-100
    issues: List[QualityIssue]
    summary: str


class QualityChecker:
    """
    Проверка качества проекта перед финальным рендером
    
    Проверяет:
    - Все ли изображения сгенерированы
    - Качество изображений (размер, формат)
    - Наличие озвучки
    - Синхронизация картинок и текста
    - SEO заполненность
    """
    
    def __init__(self):
        self.min_image_size = 50000  # Минимальный размер файла (50KB)
        self.required_image_width = 1280
        self.required_image_height = 720
    
    def check_project(self, project) -> QualityReport:
        """Полная проверка проекта"""
        issues = []
        
        # Проверка изображений
        issues.extend(self._check_images(project))
        
        # Проверка озвучки
        issues.extend(self._check_audio(project))
        
        # Проверка сценария
        issues.extend(self._check_script(project))
        
        # Проверка SEO
        issues.extend(self._check_seo(project))
        
        # Проверка синхронизации
        issues.extend(self._check_sync(project))
        
        # Подсчёт оценки
        critical_count = len([i for i in issues if i.severity == 'critical'])
        warning_count = len([i for i in issues if i.severity == 'warning'])
        
        score = 100 - (critical_count * 20) - (warning_count * 5)
        score = max(0, min(100, score))
        
        passed = critical_count == 0
        
        if passed and score >= 80:
            summary = "✅ Проект готов к рендеру"
        elif passed:
            summary = "⚠️ Проект можно рендерить, но есть замечания"
        else:
            summary = "❌ Есть критические проблемы, рендер не рекомендуется"
        
        return QualityReport(
            passed=passed,
            score=score,
            issues=issues,
            summary=summary
        )
    
    def _check_images(self, project) -> List[QualityIssue]:
        """Проверка изображений"""
        issues = []
        
        if not project.images:
            issues.append(QualityIssue(
                severity='critical',
                category='images',
                message='Нет изображений',
                fix_suggestion='Сгенерируйте изображения на вкладке Медиа'
            ))
            return issues
        
        # Проверяем каждое изображение
        missing = 0
        small = 0
        
        for i, img_path in enumerate(project.images):
            path = Path(img_path) if isinstance(img_path, str) else img_path
            
            if not path or not path.exists():
                missing += 1
                continue
            
            # Проверяем размер файла
            if path.stat().st_size < self.min_image_size:
                small += 1
        
        if missing > 0:
            issues.append(QualityIssue(
                severity='critical' if missing > len(project.images) * 0.1 else 'warning',
                category='images',
                message=f'{missing} изображений отсутствует',
                fix_suggestion='Перегенерируйте отсутствующие изображения'
            ))
        
        if small > 0:
            issues.append(QualityIssue(
                severity='warning',
                category='images',
                message=f'{small} изображений слишком маленького размера',
                fix_suggestion='Возможно это ошибки генерации, перегенерируйте'
            ))
        
        # Проверяем количество
        expected_count = len(project.image_prompts) if project.image_prompts else 0
        if expected_count > 0 and len(project.images) < expected_count * 0.9:
            issues.append(QualityIssue(
                severity='warning',
                category='images',
                message=f'Сгенерировано {len(project.images)} из {expected_count} изображений',
                fix_suggestion='Догенерируйте недостающие изображения'
            ))
        
        return issues
    
    def _check_audio(self, project) -> List[QualityIssue]:
        """Проверка озвучки"""
        issues = []
        
        if not project.audio_path:
            issues.append(QualityIssue(
                severity='critical',
                category='audio',
                message='Нет озвучки',
                fix_suggestion='Сгенерируйте озвучку на вкладке Медиа'
            ))
            return issues
        
        audio_path = Path(project.audio_path)
        if not audio_path.exists():
            issues.append(QualityIssue(
                severity='critical',
                category='audio',
                message='Файл озвучки не найден',
                fix_suggestion='Перегенерируйте озвучку'
            ))
        elif audio_path.stat().st_size < 100000:  # < 100KB подозрительно мало
            issues.append(QualityIssue(
                severity='warning',
                category='audio',
                message='Файл озвучки подозрительно маленький',
                fix_suggestion='Проверьте озвучку, возможно она неполная'
            ))
        
        return issues
    
    def _check_script(self, project) -> List[QualityIssue]:
        """Проверка сценария"""
        issues = []
        
        if not project.script:
            issues.append(QualityIssue(
                severity='critical',
                category='script',
                message='Нет сценария',
                fix_suggestion='Сгенерируйте сценарий на вкладке Сценарий'
            ))
            return issues
        
        words = len(project.script.split())
        
        # Проверяем объём
        duration_words = {
            "10-20 минут": 1500,
            "20-30 минут": 3000,
            "30-40 минут": 4500,
            "50-60 минут": 7500,
        }
        
        expected = duration_words.get(project.duration, 3000)
        if words < expected * 0.7:
            issues.append(QualityIssue(
                severity='warning',
                category='script',
                message=f'Сценарий короткий: {words} слов (ожидалось ~{expected})',
                fix_suggestion='Перегенерируйте сценарий или добавьте контент'
            ))
        
        return issues
    
    def _check_seo(self, project) -> List[QualityIssue]:
        """Проверка SEO"""
        issues = []
        
        if not project.seo_title and not project.name:
            issues.append(QualityIssue(
                severity='warning',
                category='seo',
                message='Нет заголовка для YouTube',
                fix_suggestion='Добавьте заголовок в настройках проекта'
            ))
        
        if not project.seo_tags:
            issues.append(QualityIssue(
                severity='info',
                category='seo',
                message='Нет тегов для YouTube',
                fix_suggestion='Сгенерируйте SEO на вкладке SEO'
            ))
        
        if not project.seo_description:
            issues.append(QualityIssue(
                severity='info',
                category='seo',
                message='Нет описания для YouTube',
                fix_suggestion='Сгенерируйте описание на вкладке SEO'
            ))
        
        return issues
    
    def _check_sync(self, project) -> List[QualityIssue]:
        """Проверка синхронизации"""
        issues = []
        
        if project.images and project.script:
            # Примерная проверка: достаточно ли картинок для сценария
            words = len(project.script.split())
            expected_images = words // 50  # ~1 картинка на 50 слов (30 сек)
            
            if len(project.images) < expected_images * 0.7:
                issues.append(QualityIssue(
                    severity='warning',
                    category='sync',
                    message=f'Мало изображений для сценария: {len(project.images)} (рекомендуется ~{expected_images})',
                    fix_suggestion='Добавьте больше изображений для лучшей визуализации'
                ))
        
        return issues
    
    def quick_check(self, images: List, audio_path: str, script: str) -> Dict:
        """Быстрая проверка основных компонентов"""
        result = {
            "ready": True,
            "issues": []
        }
        
        if not images:
            result["ready"] = False
            result["issues"].append("Нет изображений")
        
        if not audio_path or not Path(audio_path).exists():
            result["ready"] = False
            result["issues"].append("Нет озвучки")
        
        if not script:
            result["ready"] = False
            result["issues"].append("Нет сценария")
        
        return result
