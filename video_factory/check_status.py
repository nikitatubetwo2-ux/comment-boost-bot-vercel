import json
from pathlib import Path

with open('video_factory/output/projects.json', 'r') as f:
    data = json.load(f)

print('=== СТАТУС ПРОЕКТОВ ===')
for key, proj in data.items():
    if key.startswith('proj_'):
        name = proj.get('name', '')[:40]
        status = proj.get('status', '?')
        progress = proj.get('progress', 0)
        final = proj.get('final_video', '')
        print(f"{name}")
        print(f"  Статус: {status} | Прогресс: {progress}%")
        if final:
            print(f"  ВИДЕО: {final}")
        print()
