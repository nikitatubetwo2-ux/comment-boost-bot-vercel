#!/usr/bin/env python3
"""
Создание иконки для Video Factory
Тема: Видео + Фабрика + YouTube
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Размеры для macOS иконки
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    # Создаём основную иконку 1024x1024
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Цвета
    bg_color = (20, 163, 168)  # Teal #14a3a8
    dark_color = (13, 115, 119)  # Darker teal
    white = (255, 255, 255)
    red = (255, 0, 0)  # YouTube red
    
    # Фон - скруглённый квадрат
    margin = 80
    radius = 180
    
    # Рисуем скруглённый прямоугольник
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=bg_color
    )
    
    # Градиент эффект (тёмная полоса снизу)
    draw.rounded_rectangle(
        [margin, size//2, size - margin, size - margin],
        radius=radius,
        fill=dark_color
    )
    # Перекрываем верхнюю часть
    draw.rectangle(
        [margin, size//2, size - margin, size//2 + 100],
        fill=dark_color
    )
    
    # Кнопка Play (треугольник) - символ видео
    play_center_x = size // 2
    play_center_y = size // 2 - 50
    play_size = 200
    
    # Белый круг для кнопки play
    circle_radius = 280
    draw.ellipse(
        [play_center_x - circle_radius, play_center_y - circle_radius,
         play_center_x + circle_radius, play_center_y + circle_radius],
        fill=white
    )
    
    # Треугольник play (красный как YouTube)
    triangle_points = [
        (play_center_x - play_size//2 + 30, play_center_y - play_size//2 - 20),
        (play_center_x - play_size//2 + 30, play_center_y + play_size//2 + 20),
        (play_center_x + play_size//2 + 50, play_center_y)
    ]
    draw.polygon(triangle_points, fill=red)
    
    # Шестерёнка (символ фабрики/автоматизации) - маленькая в углу
    gear_x = size - 250
    gear_y = size - 250
    gear_radius = 80
    
    # Круг шестерёнки
    draw.ellipse(
        [gear_x - gear_radius, gear_y - gear_radius,
         gear_x + gear_radius, gear_y + gear_radius],
        fill=white
    )
    # Внутренний круг
    inner_radius = 35
    draw.ellipse(
        [gear_x - inner_radius, gear_y - inner_radius,
         gear_x + inner_radius, gear_y + inner_radius],
        fill=dark_color
    )
    
    # Зубцы шестерёнки
    import math
    for i in range(8):
        angle = i * math.pi / 4
        x1 = gear_x + int((gear_radius - 10) * math.cos(angle))
        y1 = gear_y + int((gear_radius - 10) * math.sin(angle))
        x2 = gear_x + int((gear_radius + 25) * math.cos(angle))
        y2 = gear_y + int((gear_radius + 25) * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=white, width=25)
    
    # Текст "VF" внизу
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
    except:
        font = ImageFont.load_default()
    
    text = "VF"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size - text_width) // 2
    text_y = size - 280
    draw.text((text_x, text_y), text, fill=white, font=font)
    
    # Сохраняем PNG
    png_path = "VideoFactory.app/Contents/Resources/AppIcon.png"
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    img.save(png_path, "PNG")
    print(f"✅ PNG иконка создана: {png_path}")
    
    # Создаём iconset для macOS
    iconset_path = "AppIcon.iconset"
    os.makedirs(iconset_path, exist_ok=True)
    
    for s in sizes:
        # Обычная версия
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(f"{iconset_path}/icon_{s}x{s}.png", "PNG")
        
        # @2x версия (для Retina)
        if s <= 512:
            resized_2x = img.resize((s*2, s*2), Image.Resampling.LANCZOS)
            resized_2x.save(f"{iconset_path}/icon_{s}x{s}@2x.png", "PNG")
    
    print(f"✅ Iconset создан: {iconset_path}/")
    print()
    print("📌 Чтобы создать .icns файл, выполни в Terminal:")
    print(f"   iconutil -c icns {iconset_path}")
    print(f"   mv AppIcon.icns VideoFactory.app/Contents/Resources/")
    
    return png_path


if __name__ == "__main__":
    create_icon()
