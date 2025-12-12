"""
Генератор изображений через Pollinations.ai (бесплатно, без API ключей)
"""

import requests
import urllib.parse
import time
from pathlib import Path
from typing import List, Callable, Optional
from dataclasses import dataclass


@dataclass
class ImageResult:
    """Результат генерации изображения"""
    prompt: str
    path: Optional[Path]
    success: bool
    error: Optional[str] = None


class ImageGenerator:
    """
    Генератор изображений через Pollinations.ai
    
    Особенности:
    - Полностью бесплатно
    - Без API ключей
    - Без лимитов
    - ПАРАЛЛЕЛЬНАЯ генерация (4 потока = 4x быстрее)
    """
    
    BASE_URL = "https://image.pollinations.ai/prompt/"
    
    def __init__(self, output_dir: Path = None, width: int = 1280, height: int = 720, 
                 max_workers: int = 4):
        self.output_dir = output_dir or Path("output/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = width
        self.height = height
        self.max_workers = max_workers  # Количество параллельных потоков
        self.should_stop = False
    
    def stop(self):
        """Остановить генерацию"""
        self.should_stop = True
    
    def generate_single(self, prompt: str, filename: str = None, 
                        style: str = None, seed: int = None,
                        max_retries: int = 5) -> ImageResult:
        """
        Генерация одного изображения с АГРЕССИВНЫМ автоповтором при ошибках
        
        Args:
            prompt: Текст промпта
            filename: Имя файла (без расширения)
            style: Дополнительный стиль (добавляется к промпту)
            seed: Seed для воспроизводимости
            max_retries: Максимум попыток при ошибке (по умолчанию 5)
        """
        current_prompt = prompt
        last_error = ""
        
        for attempt in range(max_retries):
            try:
                # Добавляем стиль к промпту
                full_prompt = current_prompt
                if style:
                    full_prompt = f"{current_prompt}, {style}"
                
                # Добавляем качественные параметры если их нет
                quality_tags = "8k, high quality, detailed"
                if "8k" not in full_prompt.lower():
                    full_prompt = f"{full_prompt}, {quality_tags}"
                
                # Кодируем промпт для URL
                encoded_prompt = urllib.parse.quote(full_prompt)
                
                # Формируем URL с параметрами
                url = f"{self.BASE_URL}{encoded_prompt}"
                params = {
                    "width": self.width,
                    "height": self.height,
                    "nologo": "true",
                    "seed": seed if seed else int(time.time() * 1000 + attempt)  # Разный seed каждую попытку
                }
                
                # Добавляем параметры к URL
                param_str = "&".join(f"{k}={v}" for k, v in params.items())
                full_url = f"{url}?{param_str}"
                
                print(f"[Попытка {attempt + 1}/{max_retries}] Генерация: {filename or 'image'}...")
                
                # Скачиваем изображение с меньшим таймаутом
                response = requests.get(full_url, timeout=90)
                
                # Проверяем ответ
                if response.status_code == 200:
                    content = response.content
                    
                    # Проверяем что это изображение (PNG начинается с определённых байтов)
                    is_png = content[:8] == b'\x89PNG\r\n\x1a\n'
                    is_jpeg = content[:2] == b'\xff\xd8'
                    
                    if (is_png or is_jpeg) and len(content) > 500:
                        if not filename:
                            filename = f"image_{int(time.time())}"
                        
                        filepath = self.output_dir / f"{filename}.png"
                        filepath.write_bytes(content)
                        
                        print(f"[✅] Успешно: {filename}")
                        return ImageResult(
                            prompt=prompt,
                            path=filepath,
                            success=True
                        )
                    else:
                        raise Exception(f"Ответ не является изображением (размер: {len(content)} байт)")
                else:
                    raise Exception(f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                last_error = "Таймаут запроса"
                print(f"[⏱] Таймаут, попытка {attempt + 1}/{max_retries}")
            except requests.exceptions.ConnectionError:
                last_error = "Ошибка соединения"
                print(f"[🔌] Ошибка соединения, попытка {attempt + 1}/{max_retries}")
            except Exception as e:
                last_error = str(e)
                print(f"[❌] Ошибка: {last_error}, попытка {attempt + 1}/{max_retries}")
            
            # Если не последняя попытка — упрощаем промпт и ждём
            if attempt < max_retries - 1:
                # Каждую 2-ю попытку упрощаем промпт
                if attempt >= 1:
                    current_prompt = self._simplify_prompt(current_prompt)
                    print(f"[🔄] Упрощаю промпт для следующей попытки...")
                
                # Увеличиваем паузу с каждой попыткой
                wait_time = 3 + attempt * 2
                print(f"[⏳] Жду {wait_time} сек перед следующей попыткой...")
                time.sleep(wait_time)
        
        print(f"[💀] Все {max_retries} попыток неудачны для: {filename}")
        return ImageResult(
            prompt=prompt,
            path=None,
            success=False,
            error=f"Все {max_retries} попыток неудачны: {last_error}"
        )
    
    def _simplify_prompt(self, prompt: str) -> str:
        """Умное упрощение промпта для повторной попытки — сохраняем суть, убираем проблемы"""
        simplified = prompt.lower()
        
        # Заменяем проблемные слова на безопасные альтернативы
        replacements = {
            'blood': 'red color',
            'gore': 'dramatic',
            'violent': 'intense',
            'death': 'fallen',
            'dead': 'fallen',
            'corpse': 'figure',
            'killing': 'action',
            'murder': 'conflict',
            'explosion': 'bright light',
            'fire': 'warm glow',
            'burning': 'glowing',
            'destroyed': 'damaged',
            'ruins': 'old buildings',
            'soldier': 'man in uniform',
            'military': 'uniformed',
            'weapon': 'equipment',
            'gun': 'tool',
            'rifle': 'long object',
            'tank': 'large vehicle',
            'bomb': 'object',
            'nazi': 'historical',
            'hitler': 'leader',
            'stalin': 'leader',
            'communist': 'historical',
            'fascist': 'historical',
            'war': 'historical period',
            'battle': 'historical event',
            'ww2': '1940s era',
            'wwii': '1940s era',
        }
        
        for old, new in replacements.items():
            simplified = simplified.replace(old, new)
        
        # Заменяем стиль на более безопасный
        simplified = simplified.replace('photorealistic', 'detailed digital art')
        simplified = simplified.replace('hyperrealistic', 'detailed artwork')
        simplified = simplified.replace('realistic', 'detailed')
        
        # Убираем слишком длинные промпты
        if len(simplified) > 350:
            # Оставляем первую часть (главное описание)
            simplified = simplified[:300]
        
        # Добавляем качественные теги для хорошего результата
        quality_tags = ", masterpiece, best quality, highly detailed, sharp focus, professional digital art, anatomically correct, proper proportions"
        
        if 'masterpiece' not in simplified:
            simplified = simplified.rstrip(',. ') + quality_tags
        
        return simplified
    
    def generate_batch(self, prompts: List[dict], 
                       style: str = None,
                       on_progress: Callable[[int, int, str], None] = None,
                       delay: float = 1.0) -> List[ImageResult]:
        """
        Генерация пакета изображений (последовательно)
        Используй generate_batch_parallel для быстрой генерации
        """
        results = []
        total = len(prompts)
        
        for i, prompt_data in enumerate(prompts):
            if self.should_stop:
                break
            
            if isinstance(prompt_data, dict):
                prompt = prompt_data.get('prompt_en', str(prompt_data))
                timecode = prompt_data.get('timecode', f'scene_{i+1}')
            else:
                prompt = str(prompt_data)
                timecode = f'scene_{i+1}'
            
            filename = f"{i+1:03d}_{timecode.replace(':', '-').replace(' ', '_')}"
            
            if on_progress:
                on_progress(i + 1, total, f"Генерация: {filename}")
            
            result = self.generate_single(prompt, filename, style)
            results.append(result)
            
            if i < total - 1 and not self.should_stop:
                time.sleep(delay)
        
        return results
    
    def generate_batch_parallel(self, prompts: List[dict], 
                                style: str = None,
                                on_progress: Callable[[int, int, str], None] = None,
                                on_image_ready: Callable[[int, str, bool], None] = None) -> List[ImageResult]:
        """
        ПАРАЛЛЕЛЬНАЯ генерация пакета изображений
        
        В 4 раза быстрее обычной генерации!
        100 картинок: 160 мин → 40 мин
        
        Args:
            prompts: Список промптов
            style: Общий стиль
            on_progress: Callback(current, total, status)
            on_image_ready: Callback(index, path, success) — вызывается когда картинка готова
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        total = len(prompts)
        results = [None] * total  # Предзаполняем для сохранения порядка
        completed_count = 0
        lock = threading.Lock()
        
        def generate_one(index: int, prompt_data: dict) -> tuple:
            """Генерация одной картинки с 5 попытками"""
            if self.should_stop:
                return index, ImageResult(prompt="", path=None, success=False, error="Stopped")
            
            if isinstance(prompt_data, dict):
                prompt = prompt_data.get('prompt_en', str(prompt_data))
                timecode = prompt_data.get('timecode', f'scene_{index+1}')
            else:
                prompt = str(prompt_data)
                timecode = f'scene_{index+1}'
            
            # Очищаем имя файла от проблемных символов
            safe_timecode = timecode.replace(':', '-').replace(' ', '_').replace('/', '-')
            filename = f"{index+1:03d}_{safe_timecode[:30]}"
            
            # 5 попыток на каждую картинку!
            result = self.generate_single(prompt, filename, style, max_retries=5)
            
            return index, result
        
        # Запускаем параллельную генерацию
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Отправляем все задачи
            futures = {
                executor.submit(generate_one, i, prompt): i 
                for i, prompt in enumerate(prompts)
            }
            
            # Обрабатываем результаты по мере готовности
            for future in as_completed(futures):
                if self.should_stop:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                try:
                    index, result = future.result()
                    results[index] = result
                    
                    with lock:
                        completed_count += 1
                        
                        if on_progress:
                            on_progress(completed_count, total, f"Готово: {completed_count}/{total}")
                        
                        if on_image_ready:
                            path = str(result.path) if result.success and result.path else ""
                            on_image_ready(index, path, result.success)
                            
                except Exception as e:
                    results[futures[future]] = ImageResult(
                        prompt="", path=None, success=False, error=str(e)
                    )
        
        # Заполняем None результаты ошибками
        for i, r in enumerate(results):
            if r is None:
                results[i] = ImageResult(prompt="", path=None, success=False, error="Not completed")
        
        return results


class MultiServiceGenerator:
    """
    Генератор с поддержкой нескольких сервисов
    Можно добавить другие сервисы позже
    """
    
    SERVICES = {
        "pollinations": {
            "name": "Pollinations.ai",
            "free": True,
            "quality": 3,
            "speed": 4,
            "limit": "Без лимитов"
        },
        # Можно добавить другие сервисы:
        # "replicate": {...},
        # "stability": {...},
    }
    
    def __init__(self, service: str = "pollinations", output_dir: Path = None):
        self.service = service
        self.output_dir = output_dir or Path("output/images")
        
        if service == "pollinations":
            self.generator = ImageGenerator(output_dir)
        else:
            raise ValueError(f"Неизвестный сервис: {service}")
    
    def generate(self, prompts: List[dict], **kwargs) -> List[ImageResult]:
        return self.generator.generate_batch(prompts, **kwargs)
    
    def stop(self):
        self.generator.stop()
