"""
Leonardo AI клиент для генерации превью (thumbnails)

Leonardo даёт высокое качество изображений, идеально для превью YouTube.
Поддержка ротации нескольких аккаунтов.
"""

import requests
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class LeonardoResult:
    """Результат генерации"""
    success: bool
    image_url: str = ""
    local_path: Optional[Path] = None
    error: str = ""
    generation_id: str = ""


class LeonardoClient:
    """
    Клиент Leonardo AI с ротацией ключей
    
    Для превью YouTube — генерация 3 вариантов для A/B теста
    """
    
    BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
    
    # Модели Leonardo
    MODELS = {
        "leonardo_diffusion_xl": "1e60896f-3c26-4296-8ecc-53e2afecc132",  # Лучшее качество
        "leonardo_vision_xl": "5c232a9e-9061-4777-980a-ddc8e65647c6",     # Фотореализм
        "dreamshaper_v7": "ac614f96-1082-45bf-be9d-757f2d31c174",         # Универсальный
        "absolute_reality": "e71a1c2f-4f80-4800-934f-2c68979d8cc8",       # Реализм
    }
    
    def __init__(self, api_keys: List[str] = None):
        """
        api_keys: список API ключей Leonardo для ротации
        """
        self.api_keys = [k for k in (api_keys or []) if k]
        self.current_key_index = 0
        self._update_headers()
    
    def _update_headers(self):
        """Обновление заголовков с текущим ключом"""
        current_key = self.api_keys[self.current_key_index] if self.api_keys else ""
        self.headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json"
        }
    
    def rotate_key(self):
        """Переключение на следующий ключ"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._update_headers()
            print(f"[Leonardo] Переключение на ключ #{self.current_key_index + 1}")
    
    @property
    def is_configured(self) -> bool:
        return len(self.api_keys) > 0
    
    def get_user_info(self) -> Dict:
        """Информация о пользователе и лимитах"""
        if not self.is_configured:
            return {"error": "API ключи не настроены"}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/me",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_thumbnail(
        self,
        prompt: str,
        output_path: Path,
        negative_prompt: str = "",
        model: str = "leonardo_diffusion_xl",
        width: int = 1280,
        height: int = 720,
        num_images: int = 1
    ) -> List[LeonardoResult]:
        """
        Генерация превью для YouTube
        
        Args:
            prompt: Промпт для генерации
            output_path: Папка для сохранения
            negative_prompt: Что НЕ должно быть на изображении
            model: Модель Leonardo
            width: Ширина (1280 для YouTube)
            height: Высота (720 для YouTube)
            num_images: Количество вариантов (1-4)
        
        Returns:
            Список результатов генерации
        """
        if not self.is_configured:
            return [LeonardoResult(success=False, error="API ключи не настроены")]
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Добавляем качественные теги для превью
        enhanced_prompt = f"{prompt}, youtube thumbnail style, eye-catching, vibrant colors, high contrast, professional photography, 8k, sharp focus"
        
        default_negative = "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, logo"
        full_negative = f"{negative_prompt}, {default_negative}" if negative_prompt else default_negative
        
        model_id = self.MODELS.get(model, self.MODELS["leonardo_diffusion_xl"])
        
        results = []
        
        # Пробуем все ключи при ошибке
        for attempt in range(len(self.api_keys)):
            try:
                # 1. Создаём генерацию
                gen_response = requests.post(
                    f"{self.BASE_URL}/generations",
                    headers=self.headers,
                    json={
                        "prompt": enhanced_prompt,
                        "negative_prompt": full_negative,
                        "modelId": model_id,
                        "width": width,
                        "height": height,
                        "num_images": num_images,
                        "promptMagic": True,  # Улучшение промпта
                        "highResolution": True,
                        "alchemy": True,  # Лучшее качество
                        "photoReal": True,  # Фотореализм
                        "presetStyle": "CINEMATIC"
                    },
                    timeout=60
                )
                
                if gen_response.status_code == 401 or gen_response.status_code == 403:
                    print(f"[Leonardo] Ключ #{self.current_key_index + 1} не работает, переключаю...")
                    self.rotate_key()
                    continue
                
                gen_response.raise_for_status()
                gen_data = gen_response.json()
                
                generation_id = gen_data.get("sdGenerationJob", {}).get("generationId")
                if not generation_id:
                    return [LeonardoResult(success=False, error="Не получен generation_id")]
                
                # 2. Ждём завершения генерации
                images = self._wait_for_generation(generation_id)
                
                if not images:
                    return [LeonardoResult(success=False, error="Генерация не завершилась")]
                
                # 3. Скачиваем изображения
                for i, img_data in enumerate(images):
                    img_url = img_data.get("url", "")
                    if not img_url:
                        results.append(LeonardoResult(success=False, error="Нет URL изображения"))
                        continue
                    
                    # Скачиваем
                    img_response = requests.get(img_url, timeout=60)
                    if img_response.status_code == 200:
                        file_path = output_path / f"thumbnail_variant_{i+1}.png"
                        file_path.write_bytes(img_response.content)
                        
                        results.append(LeonardoResult(
                            success=True,
                            image_url=img_url,
                            local_path=file_path,
                            generation_id=generation_id
                        ))
                    else:
                        results.append(LeonardoResult(success=False, error=f"Ошибка скачивания: {img_response.status_code}"))
                
                return results
                
            except requests.exceptions.RequestException as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    # Rate limit — переключаем ключ
                    self.rotate_key()
                    continue
                return [LeonardoResult(success=False, error=str(e))]
            except Exception as e:
                return [LeonardoResult(success=False, error=str(e))]
        
        return [LeonardoResult(success=False, error="Все ключи исчерпаны")]
    
    def _wait_for_generation(self, generation_id: str, max_wait: int = 120) -> List[Dict]:
        """Ожидание завершения генерации"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/generations/{generation_id}",
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                generation = data.get("generations_by_pk", {})
                status = generation.get("status")
                
                if status == "COMPLETE":
                    return generation.get("generated_images", [])
                elif status == "FAILED":
                    return []
                
                time.sleep(3)  # Ждём 3 секунды между проверками
                
            except Exception as e:
                print(f"[Leonardo] Ошибка проверки статуса: {e}")
                time.sleep(5)
        
        return []
    
    def generate_ab_thumbnails(
        self,
        title: str,
        topic: str,
        competitor_style: Dict = None,
        output_dir: Path = None,
        variants: int = 3
    ) -> Dict:
        """
        A/B тестирование превью — генерация нескольких вариантов
        
        Args:
            title: Заголовок видео
            topic: Тема видео
            competitor_style: Стиль конкурента (цвета, композиция)
            output_dir: Папка для сохранения
            variants: Количество вариантов (по умолчанию 3)
        
        Returns:
            {
                "variants": [...],
                "prompts": [...],
                "recommendation": "..."
            }
        """
        from core.groq_client import GroqClient, get_groq_client
        from config import config
        
        if not config.api.groq_key:
            return {"error": "Groq API не настроен"}
        
        output_dir = output_dir or Path("output/thumbnails")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        groq = get_groq_client()
        
        # Генерируем промпты для разных концепций
        style_hint = ""
        if competitor_style:
            style_hint = f"""
Стиль конкурента:
- Цвета: {competitor_style.get('colors', 'яркие, контрастные')}
- Композиция: {competitor_style.get('composition', 'центральный объект')}
- Настроение: {competitor_style.get('mood', 'драматичное')}
"""
        
        prompt = f"""Создай {variants} РАЗНЫХ концепций превью для YouTube видео.

ЗАГОЛОВОК: {title}
ТЕМА: {topic}
{style_hint}

Каждое превью должно быть КЛИКАБЕЛЬНЫМ:
- Яркие контрастные цвета
- Эмоциональное лицо ИЛИ драматичная сцена
- Простая композиция (1-2 главных элемента)
- Интрига без спойлеров

Создай {variants} РАЗНЫХ концепций:
1. Эмоциональное лицо крупным планом
2. Драматичная сцена с действием  
3. Загадочный/интригующий объект

Для каждого дай детальный промпт на английском.

Ответь в JSON:
{{
    "thumbnails": [
        {{
            "concept": "описание концепции",
            "prompt_en": "detailed english prompt for AI image generator, youtube thumbnail 1280x720, vibrant colors, high contrast, professional",
            "text_overlay": "текст для наложения (2-3 слова)"
        }}
    ]
}}"""

        response = groq._chat([
            {"role": "system", "content": "Ты эксперт по YouTube превью с CTR 15%+."},
            {"role": "user", "content": prompt}
        ])
        
        try:
            import json
            json_match = response[response.find('{'):response.rfind('}')+1]
            prompts_data = json.loads(json_match).get('thumbnails', [])
        except:
            prompts_data = []
        
        if not prompts_data:
            return {"error": "Не удалось сгенерировать промпты"}
        
        # Генерируем изображения через Leonardo
        results = []
        all_prompts = []
        
        for i, prompt_data in enumerate(prompts_data[:variants]):
            prompt_en = prompt_data.get('prompt_en', '')
            all_prompts.append({
                "concept": prompt_data.get('concept', f'Вариант {i+1}'),
                "prompt": prompt_en,
                "text_overlay": prompt_data.get('text_overlay', '')
            })
            
            if self.is_configured:
                gen_results = self.generate_thumbnail(
                    prompt=prompt_en,
                    output_path=output_dir,
                    num_images=1
                )
                
                for r in gen_results:
                    if r.success:
                        # Переименовываем файл
                        new_path = output_dir / f"variant_{i+1}_{prompt_data.get('concept', 'thumb')[:20]}.png"
                        if r.local_path and r.local_path.exists():
                            r.local_path.rename(new_path)
                            r.local_path = new_path
                        
                        results.append({
                            "variant": i + 1,
                            "concept": prompt_data.get('concept'),
                            "path": str(r.local_path) if r.local_path else None,
                            "text_overlay": prompt_data.get('text_overlay')
                        })
        
        # Сохраняем промпты в файл (для ручной генерации если нужно)
        prompts_file = output_dir / "thumbnail_prompts.txt"
        txt_content = f"ПРЕВЬЮ ДЛЯ: {title}\n{'='*50}\n\n"
        for i, p in enumerate(all_prompts, 1):
            txt_content += f"--- ВАРИАНТ {i}: {p['concept']} ---\n"
            txt_content += f"Текст: {p['text_overlay']}\n"
            txt_content += f"ПРОМПТ:\n{p['prompt']}\n\n"
        prompts_file.write_text(txt_content, encoding='utf-8')
        
        return {
            "variants": results,
            "prompts": all_prompts,
            "prompts_file": str(prompts_file),
            "recommendation": f"Сгенерировано {len(results)} вариантов. Выберите лучший для загрузки."
        }


# === ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ===

_client: Optional[LeonardoClient] = None


def get_leonardo_client() -> LeonardoClient:
    """Получение глобального клиента"""
    global _client
    if _client is None:
        from config import config
        keys = getattr(config.api, 'leonardo_keys', [])
        _client = LeonardoClient(api_keys=keys)
    return _client
