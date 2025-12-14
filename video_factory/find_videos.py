import os
from pathlib import Path

output_dir = Path('video_factory/output')

print('=== ПОИСК ГОТОВЫХ ВИДЕО ===')
for proj_dir in output_dir.glob('proj_*'):
    mp4_files = list(proj_dir.glob('*.mp4'))
    if mp4_files:
        print(f'\n{proj_dir.name}:')
        for f in mp4_files:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f'  {f.name} ({size_mb:.1f} MB)')

print('\n=== СОДЕРЖИМОЕ ПАПОК ПРОЕКТОВ ===')
for proj_dir in sorted(output_dir.glob('proj_*')):
    files = list(proj_dir.iterdir())
    print(f'\n{proj_dir.name}:')
    for f in files:
        if f.is_dir():
            count = len(list(f.iterdir()))
            print(f'  📁 {f.name}/ ({count} файлов)')
        else:
            size_kb = f.stat().st_size / 1024
            print(f'  📄 {f.name} ({size_kb:.1f} KB)')
