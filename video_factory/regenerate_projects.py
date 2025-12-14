#!/usr/bin/env python3
"""
Скрипт для сброса проектов и перегенерации с исправленными настройками

Исправления:
1. Язык — теперь сценарий генерируется на указанном языке (English)
2. Даты — пишутся прописью для правильной озвучки
3. Картинки — Ч/Б для военной тематики
4. Обложки — 3 варианта в Ч/Б для военной тематики
5. SEO — 3 кликбейтных заголовка, длинное описание
"""

import json
from pathlib import Path

projects_file = Path("video_factory/output/projects.json")

if not projects_file.exists():
    print("Файл projects.json не найден!")
    exit(1)

data = json.load(open(projects_file))

print("=== ТЕКУЩИЕ ПРОЕКТЫ ===")
for k, p in data.items():
    if k.startswith('_'):
        continue
    if not isinstance(p, dict):
        continue
    
    name = p.get('name', '')[:50]
    status = p.get('status', '?')
    lang = p.get('language', '?')
    script_len = len(p.get('script', ''))
    
    print(f"{name}")
    print(f"  Статус: {status} | Язык: {lang} | Сценарий: {script_len} символов")
    
    # Проверяем язык сценария
    script = p.get('script', '')[:200]
    if script:
        # Простая проверка — есть ли кириллица
        has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in script)
        if has_cyrillic and lang == 'English':
            print(f"  ⚠️ ПРОБЛЕМА: Сценарий на русском, но язык English!")
    print()

print("\n=== ДЕЙСТВИЯ ===")
print("1. Сбросить все проекты для перегенерации")
print("2. Сбросить только проекты с неправильным языком")
print("3. Выход")

choice = input("\nВыбор (1/2/3): ").strip()

if choice == "1":
    for k, p in data.items():
        if k.startswith('_'):
            continue
        if not isinstance(p, dict):
            continue
        
        # Сбрасываем сценарий и связанные данные
        p['script'] = ''
        p['script_segments'] = []
        p['image_prompts'] = []
        p['images'] = []
        p['thumbnails'] = []
        p['audio_path'] = ''
        p['preview_video'] = ''
        p['final_video'] = ''
        p['seo_title'] = ''
        p['seo_description'] = ''
        p['seo_tags'] = []
        p['seo_hashtags'] = []
        p['status'] = 'queued'
        p['progress'] = 0
        p['error_message'] = ''
        
        print(f"✅ Сброшен: {p.get('name', '')[:40]}")
    
    json.dump(data, open(projects_file, 'w'), ensure_ascii=False, indent=2)
    print("\n✅ Все проекты сброшены. Перезапустите очередь для перегенерации.")

elif choice == "2":
    count = 0
    for k, p in data.items():
        if k.startswith('_'):
            continue
        if not isinstance(p, dict):
            continue
        
        script = p.get('script', '')
        lang = p.get('language', '')
        
        # Проверяем — сценарий на русском но язык English
        has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in script[:500])
        
        if has_cyrillic and lang == 'English':
            p['script'] = ''
            p['script_segments'] = []
            p['status'] = 'queued'
            p['progress'] = 0
            count += 1
            print(f"✅ Сброшен: {p.get('name', '')[:40]}")
    
    if count > 0:
        json.dump(data, open(projects_file, 'w'), ensure_ascii=False, indent=2)
        print(f"\n✅ Сброшено {count} проектов с неправильным языком.")
    else:
        print("\n✅ Проектов с неправильным языком не найдено.")

else:
    print("Выход.")
