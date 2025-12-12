"""
Универсальный AI генератор превью с ротацией сервисов

Поддерживаемые сервисы (по приоритету качества):
1. Clipdrop (Stability) — 100 генераций/день БЕСПЛАТНО! ⭐⭐⭐⭐⭐
2. Segmind (SDXL/Flux) — 100 кредитов/день (обновляются!) ⭐⭐⭐⭐⭐
3. Together AI (Flux) — $25 бесплатно ⭐⭐⭐⭐⭐
4. FAL AI (Flux) — $10 бесплатно ⭐⭐⭐⭐⭐
5. Replicate (Flux/SDXL) — бесплатные кредиты ⭐⭐⭐⭐⭐
6. Fireworks AI (Flux) — $1 бесплатно ⭐⭐⭐⭐
7. Stability AI (SDXL) — 25 кредитов ⭐⭐⭐⭐
8. Novita AI (SDXL) — $0.5 бесплатно ⭐⭐⭐
9. Pollinations — бесплатно без лимитов (резерв) ⭐⭐⭐

Автоматическое переключение между сервисами при исчерпании лимитов.
Clipdrop и Segmind — лучшее качество с ежедневным обновлением лимитов!
"""

import requests
import time
import base64
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class ThumbnailResult:
    """Результат генерации превью"""
    success: bool
    path: Optional[Path] = None
    service: str = ""
    error: str = ""
    prompt: str = ""


class ThumbnailAI:
    """
    Универсальный генератор превью для YouTube
    
    Использует несколько AI сервисов с автоматической ротацией:
    - При ошибке или исчерпании лимитов переключается на следующий сервис
    - Оптимизированные настройки для превью 1280x720
    - Все сервисы хорошо генерируют людей и сцены
    """
    
    def __init__(
        self,
        clipdrop_keys: List[str] = None,
        together_keys: List[str] = None,
        fal_keys: List[str] = None,
        replicate_keys: List[str] = None,
        segmind_keys: List[str] = None,
        fireworks_keys: List[str] = None,
        stability_keys: List[str] = None,
        novita_keys: List[str] = None,
        output_dir: Path = None
    ):
        self.output_dir = output_dir or Path("output/thumbnails")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ключи для каждого сервиса (поддержка нескольких аккаунтов)
        self.clipdrop_keys = [k for k in (clipdrop_keys or []) if k]
        self.together_keys = [k for k in (together_keys or []) if k]
        self.fal_keys = [k for k in (fal_keys or []) if k]
        self.replicate_keys = [k for k in (replicate_keys or []) if k]
        self.segmind_keys = [k for k in (segmind_keys or []) if k]
        self.fireworks_keys = [k for k in (fireworks_keys or []) if k]
        self.stability_keys = [k for k in (stability_keys or []) if k]
        self.novita_keys = [k for k in (novita_keys or []) if k]
        
        # Индексы для ротации ключей
        self._clipdrop_idx = 0
        self._together_idx = 0
        self._fal_idx = 0
        self._replicate_idx = 0
        self._segmind_idx = 0
        self._fireworks_idx = 0
        self._stability_idx = 0
        self._novita_idx = 0
        
        # Порядок сервисов (по качеству, бесплатные с дневным лимитом первые)
        self.service_order = ["clipdrop", "segmind", "together", "fal", "replicate", "fireworks", "stability", "novita", "pollinations"]
        
        # Статистика использования
        self.stats = {
            "clipdrop": {"used": 0, "errors": 0},  # 100 генераций/день бесплатно!
            "segmind": {"used": 0, "errors": 0},   # 100 кредитов/день бесплатно!
            "together": {"used": 0, "errors": 0},
            "fal": {"used": 0, "errors": 0},
            "replicate": {"used": 0, "errors": 0},
            "fireworks": {"used": 0, "errors": 0},
            "stability": {"used": 0, "errors": 0},
            "novita": {"used": 0, "errors": 0},
            "pollinations": {"used": 0, "errors": 0},  # Резервный без лимитов
        }
    
    @property
    def available_services(self) -> List[str]:
        """Список доступных сервисов"""
        services = []
        if self.clipdrop_keys:
            services.append("clipdrop")
        if self.segmind_keys:
            services.append("segmind")
        if self.together_keys:
            services.append("together")
        if self.fal_keys:
            services.append("fal")
        if self.replicate_keys:
            services.append("replicate")
        if self.segmind_keys:
            services.append("segmind")
        if self.fireworks_keys:
            services.append("fireworks")
        if self.stability_keys:
            services.append("stability")
        if self.novita_keys:
            services.append("novita")
        # Pollinations всегда доступен как резервный (без API ключа)
        services.append("pollinations")
        return services
    
    def _enhance_prompt(self, prompt: str) -> str:
        """Улучшение промпта для превью"""
        # Добавляем качественные теги
        enhancements = [
            "youtube thumbnail",
            "eye-catching",
            "vibrant colors", 
            "high contrast",
            "professional photography",
            "8k",
            "sharp focus",
            "dramatic lighting"
        ]
        
        # Проверяем что теги ещё не добавлены
        prompt_lower = prompt.lower()
        to_add = [e for e in enhancements if e not in prompt_lower]
        
        if to_add:
            return f"{prompt}, {', '.join(to_add)}"
        return prompt
    
    def _get_negative_prompt(self) -> str:
        """Негативный промпт для качества"""
        return (
            "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
            "watermark, text, logo, signature, cropped, out of frame, "
            "worst quality, low resolution, pixelated"
        )
    
    # === STABILITY AI ===
    
    def _generate_stability(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Stability AI (SDXL)"""
        if not self.stability_keys:
            return ThumbnailResult(success=False, error="Нет Stability ключей", service="stability")
        
        api_key = self.stability_keys[self._stability_idx % len(self.stability_keys)]
        
        try:
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={
                    "text_prompts": [
                        {"text": self._enhance_prompt(prompt), "weight": 1},
                        {"text": self._get_negative_prompt(), "weight": -1}
                    ],
                    "cfg_scale": 7,
                    "width": 1280,
                    "height": 720,
                    "samples": 1,
                    "steps": 30,
                    "style_preset": "photographic"
                },
                timeout=120
            )
            
            if response.status_code == 401 or response.status_code == 403:
                # Ключ не работает — ротируем
                self._stability_idx += 1
                self.stats["stability"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="stability")
            
            if response.status_code == 402:
                # Кредиты закончились — ротируем
                self._stability_idx += 1
                self.stats["stability"]["errors"] += 1
                return ThumbnailResult(success=False, error="Кредиты закончились", service="stability")
            
            response.raise_for_status()
            data = response.json()
            
            # Декодируем изображение
            if data.get("artifacts"):
                image_data = base64.b64decode(data["artifacts"][0]["base64"])
                output_path = self.output_dir / f"{filename}.png"
                output_path.write_bytes(image_data)
                
                self.stats["stability"]["used"] += 1
                return ThumbnailResult(
                    success=True,
                    path=output_path,
                    service="stability",
                    prompt=prompt
                )
            
            return ThumbnailResult(success=False, error="Нет изображения в ответе", service="stability")
            
        except Exception as e:
            self.stats["stability"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="stability")
    
    # === TOGETHER AI ===
    
    def _generate_together(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Together AI (Flux)"""
        if not self.together_keys:
            return ThumbnailResult(success=False, error="Нет Together ключей", service="together")
        
        api_key = self.together_keys[self._together_idx % len(self.together_keys)]
        
        try:
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "black-forest-labs/FLUX.1-schnell-Free",  # Бесплатная модель
                    "prompt": self._enhance_prompt(prompt),
                    "width": 1280,
                    "height": 720,
                    "steps": 4,  # Flux schnell работает с малым количеством шагов
                    "n": 1,
                    "response_format": "b64_json"
                },
                timeout=120
            )
            
            if response.status_code in [401, 403]:
                self._together_idx += 1
                self.stats["together"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="together")
            
            if response.status_code == 402 or "insufficient" in response.text.lower():
                self._together_idx += 1
                self.stats["together"]["errors"] += 1
                return ThumbnailResult(success=False, error="Кредиты закончились", service="together")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and data["data"][0].get("b64_json"):
                image_data = base64.b64decode(data["data"][0]["b64_json"])
                output_path = self.output_dir / f"{filename}.png"
                output_path.write_bytes(image_data)
                
                self.stats["together"]["used"] += 1
                return ThumbnailResult(
                    success=True,
                    path=output_path,
                    service="together",
                    prompt=prompt
                )
            
            return ThumbnailResult(success=False, error="Нет изображения в ответе", service="together")
            
        except Exception as e:
            self.stats["together"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="together")
    
    # === REPLICATE ===
    
    def _generate_replicate(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Replicate (Flux/SDXL)"""
        if not self.replicate_keys:
            return ThumbnailResult(success=False, error="Нет Replicate ключей", service="replicate")
        
        api_key = self.replicate_keys[self._replicate_idx % len(self.replicate_keys)]
        
        try:
            # Создаём предсказание
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",  # Flux schnell
                    "input": {
                        "prompt": self._enhance_prompt(prompt),
                        "width": 1280,
                        "height": 720,
                        "num_outputs": 1,
                        "num_inference_steps": 4,
                        "go_fast": True
                    }
                },
                timeout=30
            )
            
            if response.status_code in [401, 403]:
                self._replicate_idx += 1
                self.stats["replicate"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="replicate")
            
            response.raise_for_status()
            prediction = response.json()
            prediction_id = prediction.get("id")
            
            if not prediction_id:
                return ThumbnailResult(success=False, error="Нет prediction_id", service="replicate")
            
            # Ждём результат
            for _ in range(60):  # Максимум 2 минуты
                time.sleep(2)
                
                status_response = requests.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {api_key}"},
                    timeout=30
                )
                status_data = status_response.json()
                
                if status_data.get("status") == "succeeded":
                    output = status_data.get("output")
                    if output and len(output) > 0:
                        # Скачиваем изображение
                        img_url = output[0]
                        img_response = requests.get(img_url, timeout=60)
                        
                        if img_response.status_code == 200:
                            output_path = self.output_dir / f"{filename}.png"
                            output_path.write_bytes(img_response.content)
                            
                            self.stats["replicate"]["used"] += 1
                            return ThumbnailResult(
                                success=True,
                                path=output_path,
                                service="replicate",
                                prompt=prompt
                            )
                    break
                
                elif status_data.get("status") == "failed":
                    error = status_data.get("error", "Unknown error")
                    return ThumbnailResult(success=False, error=error, service="replicate")
            
            return ThumbnailResult(success=False, error="Таймаут генерации", service="replicate")
            
        except Exception as e:
            self.stats["replicate"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="replicate")
    
    # === FAL AI ===
    
    def _generate_fal(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через FAL AI (Flux) — $10 бесплатно"""
        if not self.fal_keys:
            return ThumbnailResult(success=False, error="Нет FAL ключей", service="fal")
        
        api_key = self.fal_keys[self._fal_idx % len(self.fal_keys)]
        
        try:
            response = requests.post(
                "https://fal.run/fal-ai/flux/schnell",
                headers={
                    "Authorization": f"Key {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": self._enhance_prompt(prompt),
                    "image_size": {"width": 1280, "height": 720},
                    "num_inference_steps": 4,
                    "num_images": 1,
                    "enable_safety_checker": False
                },
                timeout=120
            )
            
            if response.status_code in [401, 403]:
                self._fal_idx += 1
                self.stats["fal"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="fal")
            
            if response.status_code == 402:
                self._fal_idx += 1
                self.stats["fal"]["errors"] += 1
                return ThumbnailResult(success=False, error="Кредиты закончились", service="fal")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("images") and len(data["images"]) > 0:
                img_url = data["images"][0].get("url")
                if img_url:
                    img_response = requests.get(img_url, timeout=60)
                    if img_response.status_code == 200:
                        output_path = self.output_dir / f"{filename}.png"
                        output_path.write_bytes(img_response.content)
                        
                        self.stats["fal"]["used"] += 1
                        return ThumbnailResult(success=True, path=output_path, service="fal", prompt=prompt)
            
            return ThumbnailResult(success=False, error="Нет изображения в ответе", service="fal")
            
        except Exception as e:
            self.stats["fal"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="fal")
    
    # === SEGMIND ===
    
    def _generate_segmind(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Segmind (SDXL) — 100 кредитов/день"""
        if not self.segmind_keys:
            return ThumbnailResult(success=False, error="Нет Segmind ключей", service="segmind")
        
        api_key = self.segmind_keys[self._segmind_idx % len(self.segmind_keys)]
        
        try:
            response = requests.post(
                "https://api.segmind.com/v1/sdxl1.0-txt2img",
                headers={"x-api-key": api_key},
                json={
                    "prompt": self._enhance_prompt(prompt),
                    "negative_prompt": self._get_negative_prompt(),
                    "samples": 1,
                    "scheduler": "UniPC",
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                    "seed": -1,
                    "img_width": 1280,
                    "img_height": 720,
                    "base64": True
                },
                timeout=120
            )
            
            if response.status_code in [401, 403]:
                self._segmind_idx += 1
                self.stats["segmind"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="segmind")
            
            if response.status_code == 402 or "credit" in response.text.lower():
                self._segmind_idx += 1
                self.stats["segmind"]["errors"] += 1
                return ThumbnailResult(success=False, error="Кредиты закончились", service="segmind")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("image"):
                image_data = base64.b64decode(data["image"])
                output_path = self.output_dir / f"{filename}.png"
                output_path.write_bytes(image_data)
                
                self.stats["segmind"]["used"] += 1
                return ThumbnailResult(success=True, path=output_path, service="segmind", prompt=prompt)
            
            return ThumbnailResult(success=False, error="Нет изображения в ответе", service="segmind")
            
        except Exception as e:
            self.stats["segmind"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="segmind")
    
    # === FIREWORKS AI ===
    
    def _generate_fireworks(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Fireworks AI (Flux) — $1 бесплатно"""
        if not self.fireworks_keys:
            return ThumbnailResult(success=False, error="Нет Fireworks ключей", service="fireworks")
        
        api_key = self.fireworks_keys[self._fireworks_idx % len(self.fireworks_keys)]
        
        try:
            response = requests.post(
                "https://api.fireworks.ai/inference/v1/image_generation/accounts/fireworks/models/flux-1-schnell-fp8",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": self._enhance_prompt(prompt),
                    "width": 1280,
                    "height": 720,
                    "steps": 4,
                    "cfg_scale": 1,
                    "output_format": "PNG"
                },
                timeout=120
            )
            
            if response.status_code in [401, 403]:
                self._fireworks_idx += 1
                self.stats["fireworks"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="fireworks")
            
            if response.status_code == 402:
                self._fireworks_idx += 1
                self.stats["fireworks"]["errors"] += 1
                return ThumbnailResult(success=False, error="Кредиты закончились", service="fireworks")
            
            response.raise_for_status()
            
            # Fireworks возвращает изображение напрямую
            if response.headers.get("content-type", "").startswith("image"):
                output_path = self.output_dir / f"{filename}.png"
                output_path.write_bytes(response.content)
                
                self.stats["fireworks"]["used"] += 1
                return ThumbnailResult(success=True, path=output_path, service="fireworks", prompt=prompt)
            
            return ThumbnailResult(success=False, error="Неверный формат ответа", service="fireworks")
            
        except Exception as e:
            self.stats["fireworks"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="fireworks")
    
    # === CLIPDROP (100 генераций/день БЕСПЛАТНО!) ===
    
    def _generate_clipdrop(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Clipdrop (Stability AI) — 100 генераций/день бесплатно!"""
        if not self.clipdrop_keys:
            return ThumbnailResult(success=False, error="Нет Clipdrop ключей", service="clipdrop")
        
        api_key = self.clipdrop_keys[self._clipdrop_idx % len(self.clipdrop_keys)]
        
        try:
            response = requests.post(
                "https://clipdrop-api.co/text-to-image/v1",
                headers={"x-api-key": api_key},
                files={
                    "prompt": (None, self._enhance_prompt(prompt)),
                },
                data={
                    "width": 1280,
                    "height": 720,
                },
                timeout=120
            )
            
            if response.status_code == 401:
                self._clipdrop_idx += 1
                self.stats["clipdrop"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="clipdrop")
            
            if response.status_code == 402 or response.status_code == 429:
                # Лимит исчерпан — ротируем ключ
                self._clipdrop_idx += 1
                self.stats["clipdrop"]["errors"] += 1
                return ThumbnailResult(success=False, error="Лимит исчерпан", service="clipdrop")
            
            response.raise_for_status()
            
            # Clipdrop возвращает изображение напрямую
            if response.headers.get("content-type", "").startswith("image"):
                output_path = self.output_dir / f"{filename}.png"
                output_path.write_bytes(response.content)
                
                self.stats["clipdrop"]["used"] += 1
                return ThumbnailResult(
                    success=True,
                    path=output_path,
                    service="clipdrop",
                    prompt=prompt
                )
            
            return ThumbnailResult(success=False, error="Неверный формат ответа", service="clipdrop")
            
        except Exception as e:
            self.stats["clipdrop"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="clipdrop")
    
    # === POLLINATIONS (резервный без лимитов) ===
    
    def _generate_pollinations(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Pollinations — 100% БЕСПЛАТНО без лимитов и API ключей!"""
        try:
            # Pollinations использует GET запрос с промптом в URL
            enhanced_prompt = self._enhance_prompt(prompt)
            encoded_prompt = requests.utils.quote(enhanced_prompt)
            
            # Параметры для качественной генерации
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={int(time.time())}"
            
            print(f"[Pollinations] Генерирую...")
            response = requests.get(url, timeout=120)
            
            if response.status_code == 200 and len(response.content) > 5000:
                # Определяем формат по content-type
                content_type = response.headers.get("content-type", "")
                ext = "jpg" if "jpeg" in content_type else "png"
                
                output_path = self.output_dir / f"{filename}.{ext}"
                output_path.write_bytes(response.content)
                
                self.stats["pollinations"]["used"] += 1
                return ThumbnailResult(
                    success=True,
                    path=output_path,
                    service="pollinations",
                    prompt=prompt
                )
            
            return ThumbnailResult(
                success=False,
                error=f"Ошибка: status={response.status_code}, size={len(response.content)}",
                service="pollinations"
            )
            
        except Exception as e:
            self.stats["pollinations"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="pollinations")
    
    # === NOVITA AI ===
    
    def _generate_novita(self, prompt: str, filename: str) -> ThumbnailResult:
        """Генерация через Novita AI (SDXL) — $0.5 бесплатно"""
        if not self.novita_keys:
            return ThumbnailResult(success=False, error="Нет Novita ключей", service="novita")
        
        api_key = self.novita_keys[self._novita_idx % len(self.novita_keys)]
        
        try:
            response = requests.post(
                "https://api.novita.ai/v3/async/txt2img",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model_name": "sd_xl_base_1.0.safetensors",
                    "prompt": self._enhance_prompt(prompt),
                    "negative_prompt": self._get_negative_prompt(),
                    "width": 1280,
                    "height": 720,
                    "steps": 25,
                    "guidance_scale": 7.5,
                    "sampler_name": "DPM++ 2M Karras"
                },
                timeout=30
            )
            
            if response.status_code in [401, 403]:
                self._novita_idx += 1
                self.stats["novita"]["errors"] += 1
                return ThumbnailResult(success=False, error="Ключ не работает", service="novita")
            
            response.raise_for_status()
            data = response.json()
            task_id = data.get("task_id")
            
            if not task_id:
                return ThumbnailResult(success=False, error="Нет task_id", service="novita")
            
            # Ждём результат
            for _ in range(60):
                time.sleep(2)
                
                status_response = requests.get(
                    f"https://api.novita.ai/v3/async/task-result?task_id={task_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30
                )
                status_data = status_response.json()
                
                if status_data.get("task", {}).get("status") == "TASK_STATUS_SUCCEED":
                    images = status_data.get("images", [])
                    if images:
                        img_url = images[0].get("image_url")
                        if img_url:
                            img_response = requests.get(img_url, timeout=60)
                            if img_response.status_code == 200:
                                output_path = self.output_dir / f"{filename}.png"
                                output_path.write_bytes(img_response.content)
                                
                                self.stats["novita"]["used"] += 1
                                return ThumbnailResult(success=True, path=output_path, service="novita", prompt=prompt)
                    break
                
                elif status_data.get("task", {}).get("status") == "TASK_STATUS_FAILED":
                    return ThumbnailResult(success=False, error="Генерация не удалась", service="novita")
            
            return ThumbnailResult(success=False, error="Таймаут генерации", service="novita")
            
        except Exception as e:
            self.stats["novita"]["errors"] += 1
            return ThumbnailResult(success=False, error=str(e), service="novita")
    
    # === ГЛАВНЫЙ МЕТОД ===
    
    def generate(self, prompt: str, filename: str = "thumbnail") -> ThumbnailResult:
        """
        Генерация превью с автоматической ротацией сервисов
        
        Пробует сервисы по порядку качества, при ошибке переключается на следующий
        """
        available = self.available_services
        
        if not available:
            return ThumbnailResult(
                success=False,
                error="Нет настроенных сервисов. Добавьте API ключи в .env"
            )
        
        errors = []
        
        for service in self.service_order:
            if service not in available:
                continue
            
            print(f"[ThumbnailAI] Пробую {service}...")
            
            if service == "clipdrop":
                result = self._generate_clipdrop(prompt, filename)
            elif service == "pollinations":
                result = self._generate_pollinations(prompt, filename)
            elif service == "together":
                result = self._generate_together(prompt, filename)
            elif service == "fal":
                result = self._generate_fal(prompt, filename)
            elif service == "replicate":
                result = self._generate_replicate(prompt, filename)
            elif service == "segmind":
                result = self._generate_segmind(prompt, filename)
            elif service == "fireworks":
                result = self._generate_fireworks(prompt, filename)
            elif service == "stability":
                result = self._generate_stability(prompt, filename)
            elif service == "novita":
                result = self._generate_novita(prompt, filename)
            else:
                continue
            
            if result.success:
                print(f"[ThumbnailAI] ✅ Успех через {service}")
                return result
            else:
                errors.append(f"{service}: {result.error}")
                print(f"[ThumbnailAI] ❌ {service}: {result.error}")
        
        return ThumbnailResult(
            success=False,
            error=f"Все сервисы не сработали: {'; '.join(errors)}"
        )
    
    def generate_variants(self, prompt: str, count: int = 3, base_filename: str = "thumb") -> List[ThumbnailResult]:
        """
        Генерация нескольких вариантов превью для A/B теста
        """
        results = []
        
        for i in range(count):
            # Немного варьируем промпт для разнообразия
            variant_prompt = prompt
            if i == 1:
                variant_prompt = f"{prompt}, close-up shot"
            elif i == 2:
                variant_prompt = f"{prompt}, wide angle, dramatic perspective"
            
            result = self.generate(variant_prompt, f"{base_filename}_v{i+1}")
            results.append(result)
            
            # Пауза между генерациями
            if i < count - 1:
                time.sleep(2)
        
        return results
    
    def get_stats(self) -> Dict:
        """Статистика использования сервисов"""
        return {
            "available_services": self.available_services,
            "stats": self.stats,
            "total_generated": sum(s["used"] for s in self.stats.values()),
            "total_errors": sum(s["errors"] for s in self.stats.values())
        }


# === ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ===

_thumbnail_ai: Optional[ThumbnailAI] = None


def get_thumbnail_ai() -> ThumbnailAI:
    """Получение глобального экземпляра"""
    global _thumbnail_ai
    if _thumbnail_ai is None:
        from config import config
        
        _thumbnail_ai = ThumbnailAI(
            clipdrop_keys=getattr(config.api, 'clipdrop_keys', []),
            together_keys=getattr(config.api, 'together_keys', []),
            fal_keys=getattr(config.api, 'fal_keys', []),
            replicate_keys=getattr(config.api, 'replicate_keys', []),
            segmind_keys=getattr(config.api, 'segmind_keys', []),
            fireworks_keys=getattr(config.api, 'fireworks_keys', []),
            stability_keys=getattr(config.api, 'stability_keys', []),
            novita_keys=getattr(config.api, 'novita_keys', [])
        )
    return _thumbnail_ai
