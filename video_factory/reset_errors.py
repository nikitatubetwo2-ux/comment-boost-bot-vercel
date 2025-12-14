import json

with open('video_factory/output/projects.json', 'r') as f:
    data = json.load(f)

reset_count = 0
for key, proj in data.items():
    if key.startswith('proj_'):
        if proj.get('status') == 'error':
            proj['status'] = 'queued'
            proj['error_message'] = ''
            print(f"Сброшен: {proj.get('name', '')[:40]}")
            reset_count += 1

with open('video_factory/output/projects.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nСброшено {reset_count} проектов")
