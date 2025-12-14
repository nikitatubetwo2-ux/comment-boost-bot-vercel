#!/usr/bin/env python3
"""Копирование готового видео на рабочий стол"""
import shutil
from pathlib import Path

# Исходная папка
src_dir = Path("video_factory/output/proj_1765542226_0")

# Название проекта
video_name = "Как одна неделя в октябре 1944 года изменила ход войны"

# Папка на рабочем столе
desktop_dir = Path.home() / "Desktop" / "VideoFactory_Ready" / video_name
desktop_dir.mkdir(parents=True, exist_ok=True)

# Копируем видео
video_file = src_dir / "Как одна неделя в октябре 1944 года изменила ход в_preview.mp4"
if video_file.exists():
    dest = desktop_dir / f"{video_name}.mp4"
    print(f"Копирую видео: {video_file.name}")
    shutil.copy2(video_file, dest)
    print(f"✅ Видео скопировано: {dest}")

# Копируем превью/обложки
thumbnails_dir = src_dir / "thumbnails"
if thumbnails_dir.exists():
    for thumb in thumbnails_dir.glob("*.*"):
        if thumb.suffix in ['.webp', '.png', '.jpg']:
            shutil.copy2(thumb, desktop_dir / thumb.name)
            print(f"✅ Обложка: {thumb.name}")

# Читаем данные для SEO
preview_data = src_dir / "preview_data.json"
seo_content = f"""=== SEO для YouTube ===

📌 ЗАГОЛОВОК:
{video_name}

📝 ОПИСАНИЕ:
Документальное видео о ключевых событиях октября 1944 года во Второй мировой войне.

🏷️ ТЕГИ:
Вторая мировая война, 1944, история, документальный фильм, WW2

#️⃣ ХЕШТЕГИ:
#WW2 #История #Документальный #1944
"""

seo_file = desktop_dir / "SEO.txt"
seo_file.write_text(seo_content, encoding="utf-8")
print(f"✅ SEO файл создан")

print(f"\n🎉 ГОТОВО! Папка: {desktop_dir}")
