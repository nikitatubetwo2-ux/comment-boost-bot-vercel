"""
Экспорт проекта — все файлы в одну папку
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ExportResult:
    """Результат экспорта"""
    success: bool
    export_path: Path
    files: List[str]
    message: str


class ProjectExporter:
    """Экспортёр проекта"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def export_project(
        self,
        project_name: str,
        video_path: Optional[Path] = None,
        srt_path: Optional[Path] = None,
        thumbnail_paths: List[Path] = None,
        script_text: str = "",
        seo_data: Dict[str, Any] = None,
        include_prompts: bool = True,
        image_prompts: List[str] = None,
        preview_prompts: List[str] = None
    ) -> ExportResult:
        """Экспорт всех файлов проекта"""
        
        # Создаём папку экспорта
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in '-_ ' else '_' for c in project_name)
        export_dir = self.output_dir / f"{safe_name}_{timestamp}"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        try:
            # Видео
            if video_path and video_path.exists():
                dest = export_dir / f"{safe_name}.mp4"
                shutil.copy2(video_path, dest)
                exported_files.append(str(dest.name))
            
            # Субтитры
            if srt_path and srt_path.exists():
                dest = export_dir / f"{safe_name}.srt"
                shutil.copy2(srt_path, dest)
                exported_files.append(str(dest.name))
            
            # Превью
            if thumbnail_paths:
                thumbs_dir = export_dir / "thumbnails"
                thumbs_dir.mkdir(exist_ok=True)
                for i, thumb in enumerate(thumbnail_paths):
                    if thumb.exists():
                        dest = thumbs_dir / f"thumbnail_{i+1}{thumb.suffix}"
                        shutil.copy2(thumb, dest)
                        exported_files.append(f"thumbnails/{dest.name}")
            
            # Сценарий
            if script_text:
                script_path = export_dir / f"{safe_name}_script.txt"
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script_text)
                exported_files.append(script_path.name)
            
            # SEO данные
            if seo_data:
                seo_path = export_dir / "seo.json"
                with open(seo_path, 'w', encoding='utf-8') as f:
                    json.dump(seo_data, f, indent=2, ensure_ascii=False)
                exported_files.append("seo.json")
                
                # Также создаём текстовый файл для удобства
                seo_txt_path = export_dir / "seo_for_youtube.txt"
                with open(seo_txt_path, 'w', encoding='utf-8') as f:
                    f.write("=== ЗАГОЛОВОК ===\n")
                    f.write(seo_data.get('title', project_name) + "\n\n")
                    
                    f.write("=== ОПИСАНИЕ ===\n")
                    f.write(seo_data.get('description', '') + "\n\n")
                    
                    f.write("=== ТЕГИ ===\n")
                    f.write(', '.join(seo_data.get('tags', [])) + "\n\n")
                    
                    f.write("=== ХЕШТЕГИ ===\n")
                    f.write(' '.join(seo_data.get('hashtags', [])) + "\n")
                
                exported_files.append("seo_for_youtube.txt")
            
            # Промпты для изображений
            if include_prompts and image_prompts:
                prompts_path = export_dir / "image_prompts.txt"
                with open(prompts_path, 'w', encoding='utf-8') as f:
                    for i, prompt in enumerate(image_prompts, 1):
                        f.write(f"=== Изображение {i} ===\n")
                        f.write(f"{prompt}\n\n")
                exported_files.append("image_prompts.txt")
            
            # Промпты для превью
            if include_prompts and preview_prompts:
                preview_path = export_dir / "preview_prompts.txt"
                with open(preview_path, 'w', encoding='utf-8') as f:
                    for i, prompt in enumerate(preview_prompts, 1):
                        f.write(f"=== Превью {i} ===\n")
                        f.write(f"{prompt}\n\n")
                exported_files.append("preview_prompts.txt")
            
            # README
            readme_path = export_dir / "README.txt"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"Проект: {project_name}\n")
                f.write(f"Дата экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Создано в Video Factory\n\n")
                f.write("Содержимое:\n")
                for file in exported_files:
                    f.write(f"  - {file}\n")
                f.write("\n")
                f.write("Инструкция:\n")
                f.write("1. Загрузите видео на YouTube\n")
                f.write("2. Скопируйте заголовок из seo_for_youtube.txt\n")
                f.write("3. Скопируйте описание\n")
                f.write("4. Добавьте теги\n")
                f.write("5. Загрузите превью из папки thumbnails\n")
                f.write("6. Загрузите субтитры (.srt файл)\n")
            exported_files.append("README.txt")
            
            return ExportResult(
                success=True,
                export_path=export_dir,
                files=exported_files,
                message=f"Экспортировано {len(exported_files)} файлов"
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                export_path=export_dir,
                files=exported_files,
                message=f"Ошибка: {str(e)}"
            )
    
    def create_upload_checklist(self, export_dir: Path) -> Path:
        """Создание чеклиста для загрузки"""
        
        checklist_path = export_dir / "upload_checklist.txt"
        
        with open(checklist_path, 'w', encoding='utf-8') as f:
            f.write("📋 ЧЕКЛИСТ ЗАГРУЗКИ НА YOUTUBE\n")
            f.write("=" * 40 + "\n\n")
            
            f.write("[ ] 1. Загрузить видео файл (.mp4)\n")
            f.write("[ ] 2. Установить заголовок\n")
            f.write("[ ] 3. Добавить описание\n")
            f.write("[ ] 4. Добавить теги\n")
            f.write("[ ] 5. Загрузить превью\n")
            f.write("[ ] 6. Добавить субтитры (.srt)\n")
            f.write("[ ] 7. Выбрать категорию\n")
            f.write("[ ] 8. Настроить возрастные ограничения\n")
            f.write("[ ] 9. Добавить конечные заставки\n")
            f.write("[ ] 10. Добавить подсказки\n")
            f.write("[ ] 11. Запланировать публикацию\n")
            f.write("[ ] 12. Проверить монетизацию\n")
            f.write("\n")
            f.write("Удачной публикации! 🚀\n")
        
        return checklist_path
