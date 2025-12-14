"""
FLUX генератор изображений через Hugging Face Spaces

БЕСПЛАТНО с ротацией аккаунтов!
Качество как у Grok — топовое для людей и военной тематики.

Использует FLUX.1-dev от Black Forest Labs.
"""

import shutil
import time
import os
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass
from gradio_client import Client


@dataclass
class FluxResult:
    """Результат генерации"""
    success: bool
    path: Optional[Path] = None
    error: str = ""
    seed: int = 0
    generation_time: float = 0
    token_used: str = ""


class FluxGenerator:
    """
    Генератор изображений на базе FLUX через Hugging Face Spaces
    
    Особенности:
    - Ротация токенов при исчерпании лимита GPU
    - FLUX.1-dev для максимального качества
    - Автоматическое переключение между аккаунтами
    """
    
    def __init__(
        self,
        hf_tokens: List[str] = None,
        output_dir: Path = None,
        use_dev: bool = True  # True = FLUX.1-dev (лучше), False = schnell (быстрее)
    ):
        self.output_dir = output_dir or Path("output/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Токены для ротации
        self.hf_tokens = [t for t in (hf_tokens or []) if t and t.startswith("hf_")]
        self._current_token_idx = 0
        
        # Клиенты для каждого токена (ленивая инициализация)
        self._clients = {}
        
        # Какую модель использовать
        self.use_dev = use_dev
        self.space_name = "black-forest-labs/FLUX.1-dev" if use_dev else "black-forest-labs/FLUX.1-schnell"
        
        # Статистика
        self.stats = {
            "generated": 0,
            "errors": 0,
            "total_time": 0,
            "token_switches": 0
        }
        
        # Трекинг лимитов токенов
        self._token_cooldowns = {}  # token -> время когда можно снова использовать
        self._cooldown_file = self.output_dir.parent / "hf_cooldowns.json"
        self._load_cooldowns()  # Загружаем сохранённые cooldowns
        
        # Для параллельной работы — какие токены сейчас используются
        self._tokens_in_use = set()
        self._token_lock = None  # Инициализируем при первом использовании
    
    def _get_client(self, token: str = None) -> Client:
        """Получение клиента для токена"""
        import os
        
        if token and token not in self._clients:
            print(f"[FLUX] Подключаюсь с токеном ...{token[-8:]}")
            # Устанавливаем токен через переменную окружения
            os.environ["HF_TOKEN"] = token
            self._clients[token] = Client(self.space_name)
        elif not token and None not in self._clients:
            print(f"[FLUX] Подключаюсь без токена...")
            if "HF_TOKEN" in os.environ:
                del os.environ["HF_TOKEN"]
            self._clients[None] = Client(self.space_name)
        
        # Устанавливаем текущий токен
        if token:
            os.environ["HF_TOKEN"] = token
        
        return self._clients.get(token) or self._clients.get(None)
    
    def _get_available_token(self, for_parallel: bool = False) -> Optional[str]:
        """
        Получение доступного токена (не в cooldown и не используется)
        
        ВАЖНО: Эта функция НИКОГДА не возвращает ошибку!
        Если все токены в cooldown — ждёт пока хотя бы один освободится.
        Это гарантирует что проект НЕ уйдёт в ошибку из-за квот.
        """
        import threading
        
        # Ленивая инициализация lock
        if self._token_lock is None:
            self._token_lock = threading.Lock()
        
        wait_time = 0
        
        # Если нет токенов — работаем без токена
        if not self.hf_tokens:
            return None
        
        while True:  # Бесконечный цикл пока не найдём токен
            now = time.time()
            
            with self._token_lock:
                # Ищем токен не в cooldown и не используемый
                for i in range(len(self.hf_tokens)):
                    idx = (self._current_token_idx + i) % len(self.hf_tokens)
                    token = self.hf_tokens[idx]
                    
                    cooldown_until = self._token_cooldowns.get(token, 0)
                    is_available = now >= cooldown_until
                    is_free = token not in self._tokens_in_use
                    
                    if is_available and (is_free or not for_parallel):
                        self._current_token_idx = (idx + 1) % len(self.hf_tokens)
                        if for_parallel:
                            self._tokens_in_use.add(token)
                        return token
                
                # Все токены заняты или в cooldown
                available_tokens = [t for t in self.hf_tokens if t not in self._tokens_in_use]
                
                if not available_tokens:
                    # Все токены используются другими потоками — короткое ожидание
                    wait_time = 5
                else:
                    # Находим токен который раньше освободится
                    min_cooldown_token = min(available_tokens, key=lambda t: self._token_cooldowns.get(t, 0))
                    wait_time = self._token_cooldowns.get(min_cooldown_token, 0) - now
                    
                    if wait_time <= 0:
                        # Токен уже доступен — пробуем снова
                        continue
                    
                    # Показываем статус ожидания
                    mins = int(wait_time / 60)
                    available_count = sum(1 for t in self.hf_tokens if self._token_cooldowns.get(t, 0) <= now)
                    print(f"[FLUX] ⏳ Все {len(self.hf_tokens)} токенов в cooldown ({available_count} доступно)")
                    print(f"[FLUX] 💤 Ожидание {mins} мин до восстановления квоты...")
            
            # Ждём вне lock чтобы не блокировать другие потоки
            if wait_time > 0:
                # Ждём порциями по 10 минут с логированием
                wait_interval = 600  # 10 минут
                total_waited = 0
                
                while total_waited < wait_time:
                    actual_wait = min(wait_interval, wait_time - total_waited)
                    time.sleep(actual_wait)
                    total_waited += actual_wait
                    
                    # Проверяем не освободился ли токен раньше
                    now = time.time()
                    available_count = sum(1 for t in self.hf_tokens if self._token_cooldowns.get(t, 0) <= now)
                    
                    if available_count > 0:
                        print(f"[FLUX] ✅ Токен освободился! Продолжаю генерацию...")
                        break
                    
                    remaining = int((wait_time - total_waited) / 60)
                    if remaining > 0:
                        print(f"[FLUX] ⏳ Ещё {remaining} мин до восстановления квоты...")
    
    def _release_token(self, token: str):
        """Освободить токен после использования"""
        if self._token_lock and token:
            with self._token_lock:
                self._tokens_in_use.discard(token)
    
    def _load_cooldowns(self):
        """Загрузка сохранённых cooldowns из файла"""
        import json
        try:
            if self._cooldown_file.exists():
                with open(self._cooldown_file, 'r') as f:
                    data = json.load(f)
                    self._token_cooldowns = data.get('cooldowns', {})
                    
                    # Показываем статус при загрузке
                    now = time.time()
                    available = sum(1 for t in self.hf_tokens if self._token_cooldowns.get(t, 0) <= now)
                    in_cooldown = len(self.hf_tokens) - available
                    
                    if in_cooldown > 0:
                        print(f"[FLUX] Загружены cooldowns: {available}/{len(self.hf_tokens)} токенов доступно")
        except Exception as e:
            print(f"[FLUX] Не удалось загрузить cooldowns: {e}")
            self._token_cooldowns = {}
    
    def _save_cooldowns(self):
        """Сохранение cooldowns в файл"""
        import json
        try:
            with open(self._cooldown_file, 'w') as f:
                json.dump({'cooldowns': self._token_cooldowns}, f)
        except Exception as e:
            print(f"[FLUX] Не удалось сохранить cooldowns: {e}")
    
    def _mark_token_cooldown(self, token: str, seconds: int = 5400):
        """
        Пометить токен как в cooldown
        
        По умолчанию 5400 секунд (1.5 часа) — время восстановления GPU квоты на HuggingFace.
        Это предотвращает постоянные запросы на исчерпанные аккаунты.
        """
        self._token_cooldowns[token] = time.time() + seconds
        self.stats["token_switches"] += 1
        self._save_cooldowns()  # Сохраняем в файл
        
        # Показываем сколько токенов доступно
        now = time.time()
        available = sum(1 for t in self.hf_tokens if self._token_cooldowns.get(t, 0) <= now)
        in_cooldown = len(self.hf_tokens) - available
        
        hours = seconds / 3600
        print(f"[FLUX] Токен ...{token[-8:] if token else 'none'} в cooldown на {hours:.1f}ч")
        print(f"[FLUX] Доступно: {available}/{len(self.hf_tokens)} токенов ({in_cooldown} в cooldown)")
    
    def generate(
        self,
        prompt: str,
        filename: str = "image",
        width: int = 1280,
        height: int = 720,
        steps: int = 28,
        guidance: float = 3.5,
        seed: int = 0,
        randomize_seed: bool = True,
        enhance_prompt: bool = True,
        max_retries: int = 3,
        for_parallel: bool = False
    ) -> FluxResult:
        """
        Генерация изображения с автоматической ротацией токенов
        
        Args:
            for_parallel: True если вызывается из параллельной генерации
                         (токен будет заблокирован на время использования)
        """
        start_time = time.time()
        
        # Улучшаем промпт для военной тематики
        if enhance_prompt:
            prompt = self._enhance_prompt(prompt)
        
        last_error = ""
        current_token = None
        
        for attempt in range(max_retries):
            # Получаем токен (с блокировкой для параллельной работы)
            token = self._get_available_token(for_parallel=for_parallel)
            
            # Если токен не получен — ждём и пробуем снова
            if token is None and for_parallel:
                time.sleep(5)
                continue
            
            current_token = token
            
            try:
                client = self._get_client(token)
                
                print(f"[FLUX] Генерирую ({attempt+1}/{max_retries}): {prompt[:50]}...")
                
                if self.use_dev:
                    # FLUX.1-dev параметры
                    result = client.predict(
                        prompt=prompt,
                        seed=seed,
                        randomize_seed=randomize_seed,
                        width=min(width, 1440),
                        height=min(height, 1440),
                        guidance_scale=guidance,
                        num_inference_steps=steps,
                        api_name="/infer"
                    )
                else:
                    # FLUX.1-schnell параметры
                    result = client.predict(
                        prompt=prompt,
                        seed=seed,
                        randomize_seed=randomize_seed,
                        width=min(width, 1440),
                        height=min(height, 1440),
                        num_inference_steps=4,
                        api_name="/infer"
                    )
                
                # Успех!
                temp_path = result[0]
                used_seed = result[1] if len(result) > 1 else 0
                
                output_path = self.output_dir / f"{filename}.webp"
                shutil.copy(temp_path, output_path)
                
                generation_time = time.time() - start_time
                self.stats["generated"] += 1
                self.stats["total_time"] += generation_time
                
                print(f"[FLUX] ✅ Готово за {generation_time:.1f}с: {output_path.name}")
                
                # Освобождаем токен при успехе
                if for_parallel and current_token:
                    self._release_token(current_token)
                
                return FluxResult(
                    success=True,
                    path=output_path,
                    seed=used_seed,
                    generation_time=generation_time,
                    token_used=f"...{token[-8:]}" if token else "none"
                )
                
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                
                # Проверяем тип ошибки
                if "GPU quota" in error_msg or "exceeded" in error_msg.lower():
                    # Лимит GPU — ставим токен в cooldown на 1.5 часа
                    self._mark_token_cooldown(token, 5400)  # 1.5 часа для восстановления квоты
                    if for_parallel and current_token:
                        self._release_token(current_token)
                    current_token = None
                    continue
                    
                elif "rate limit" in error_msg.lower():
                    # Rate limit — короткий cooldown
                    self._mark_token_cooldown(token, 60)
                    if for_parallel and current_token:
                        self._release_token(current_token)
                    current_token = None
                    continue
                    
                elif "content" in error_msg.lower() or "safety" in error_msg.lower() or "nsfw" in error_msg.lower():
                    # Контент заблокирован — перефразируем промпт
                    print(f"[FLUX] ⚠️ Контент заблокирован, перефразирую промпт...")
                    prompt = self._rephrase_prompt(prompt, attempt + 1)
                    continue
                    
                else:
                    # Другая ошибка — пробуем с другой вариацией промпта
                    print(f"[FLUX] ❌ Ошибка: {error_msg[:100]}")
                    if attempt < max_retries - 1:
                        prompt = self._enhance_prompt(prompt, attempt + 1)
                        print(f"[FLUX] 🔄 Пробую с изменённым промптом...")
                    self.stats["errors"] += 1
        
        # Освобождаем токен при неудаче
        if for_parallel and current_token:
            self._release_token(current_token)
        
        # Если ошибка связана с квотой — пробуем ещё раз после ожидания
        if "GPU quota" in last_error or "exceeded" in last_error.lower():
            print(f"[FLUX] 🔄 Все попытки исчерпаны из-за квот, жду и пробую снова...")
            time.sleep(60)  # Ждём минуту
            return self.generate(
                prompt=prompt.split(',')[0],  # Упрощаем промпт
                filename=filename,
                width=width,
                height=height,
                steps=steps,
                guidance=guidance,
                seed=seed,
                randomize_seed=randomize_seed,
                enhance_prompt=True,
                max_retries=max_retries,
                for_parallel=for_parallel
            )
        
        return FluxResult(success=False, error=last_error)
    
    def _enhance_prompt(self, prompt: str, variation: int = 0) -> str:
        """
        Улучшение промпта для военной тематики
        variation: 0-5 для разных вариаций при перегенерации
        """
        prompt_lower = prompt.lower()
        
        # Базовые улучшения качества — разные варианты
        quality_tags = [
            "extremely detailed, photorealistic, 8k resolution, sharp focus",
            "ultra high definition, cinematic quality, professional photography",
            "masterpiece, best quality, highly detailed, crisp details",
            "stunning detail, hyperrealistic, award-winning photography",
            "exceptional clarity, museum quality, fine art photography"
        ]
        
        # Стиль фото для военной тематики — больше вариаций
        photo_styles = [
            "authentic documentary photograph, Kodachrome film, 1940s war photography, Robert Capa style",
            "cinematic war photography, dramatic lighting, film grain texture, historical accuracy",
            "historical photograph, sepia undertones, natural lighting, archival quality",
            "epic war scene, dramatic composition, golden hour lighting, atmospheric",
            "gritty documentary style, authentic period details, raw emotion captured",
            "vintage war photography aesthetic, muted colors, powerful composition"
        ]
        
        # Улучшения для лиц и людей
        face_quality = [
            "detailed realistic faces, accurate human anatomy, natural proportions",
            "lifelike facial features, natural skin texture, expressive eyes",
            "photorealistic portraits, correct hand anatomy, proper body proportions",
            "authentic human features, symmetrical face, natural expressions",
            "detailed character study, realistic skin tones, proper lighting on faces"
        ]
        
        # Атмосферные добавки для военной тематики
        atmosphere = [
            "dust particles in air, smoke in background, dramatic shadows",
            "moody atmosphere, volumetric lighting, cinematic depth",
            "war-torn environment, authentic period setting, emotional impact",
            "battlefield atmosphere, tension in the air, historical moment",
            "grim reality of war, powerful storytelling, documentary feel"
        ]
        
        # Выбираем вариации
        style_idx = variation % len(photo_styles)
        face_idx = variation % len(face_quality)
        quality_idx = variation % len(quality_tags)
        atmo_idx = variation % len(atmosphere)
        
        additions = []
        
        # Добавляем качество
        additions.append(quality_tags[quality_idx])
        
        # Добавляем стиль фото если нет
        if "photograph" not in prompt_lower and "photo" not in prompt_lower:
            additions.append(photo_styles[style_idx])
        
        # Добавляем качество лиц для сцен с людьми
        human_keywords = ["soldier", "officer", "man", "woman", "people", "troops", "army", "person"]
        if any(kw in prompt_lower for kw in human_keywords):
            additions.append(face_quality[face_idx])
        
        # Добавляем атмосферу для военных сцен
        war_keywords = ["war", "battle", "military", "ww2", "wwii", "combat", "soldier"]
        if any(kw in prompt_lower for kw in war_keywords):
            additions.append(atmosphere[atmo_idx])
        
        # Финальные теги
        final_tags = "masterpiece, award winning, national geographic quality"
        
        return f"{prompt}, {', '.join(additions)}, {final_tags}"
    
    def _rephrase_prompt(self, original_prompt: str, attempt: int) -> str:
        """Перефразировка промпта при ошибке генерации"""
        # Извлекаем основную идею
        base = original_prompt.split(',')[0].strip()
        
        # Убираем потенциально проблемные слова
        problematic = ['blood', 'gore', 'death', 'dead', 'corpse', 'kill', 'violent', 'graphic']
        for word in problematic:
            base = base.replace(word, 'fallen')
        
        # Разные подходы к перефразировке
        rephrase_strategies = [
            # Упрощаем и делаем безопаснее
            f"Historical documentary scene: {base}, cinematic photography, 8k, professional",
            # Меняем на художественный стиль
            f"Artistic interpretation of {base}, oil painting style, museum quality, dramatic lighting",
            # Делаем более абстрактным
            f"Symbolic representation of {base}, atmospheric, moody, artistic photography",
            # Фокус на атмосфере
            f"Atmospheric scene depicting {base}, soft lighting, historical accuracy, detailed",
            # Максимально нейтральный
            f"Historical moment: {base}, documentary style, respectful portrayal, high quality"
        ]
        
        return rephrase_strategies[attempt % len(rephrase_strategies)]
    
    def generate_thumbnail(self, prompt: str, filename: str = "thumbnail") -> FluxResult:
        """Генерация превью для YouTube"""
        enhanced = f"{prompt}, youtube thumbnail, eye-catching, vibrant colors, dramatic composition"
        return self.generate(enhanced, filename, width=1280, height=720, steps=28)
    
    def generate_batch(
        self,
        prompts: List[str],
        base_filename: str = "image",
        delay: float = 2.0
    ) -> List[FluxResult]:
        """Пакетная генерация с задержкой (последовательная)"""
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"\n[FLUX] Пакет: {i+1}/{len(prompts)}")
            result = self.generate(prompt, f"{base_filename}_{i+1:03d}")
            results.append(result)
            
            if i < len(prompts) - 1:
                time.sleep(delay)
        
        return results
    
    def generate_parallel(
        self,
        prompts: List[str],
        base_filename: str = "image",
        max_workers: int = 4,
        on_progress: Callable = None
    ) -> List[FluxResult]:
        """
        ПАРАЛЛЕЛЬНАЯ генерация изображений
        
        Использует несколько токенов одновременно для ускорения.
        С 16 токенами можно генерировать 4-8 изображений параллельно.
        
        Args:
            prompts: Список промптов
            base_filename: Базовое имя файла
            max_workers: Максимум параллельных генераций (рекомендуется 4-8)
            on_progress: Callback для прогресса (index, total, result)
        
        Returns:
            Список результатов в том же порядке что и промпты
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        # Ограничиваем воркеры количеством токенов
        actual_workers = min(max_workers, len(self.hf_tokens)) if self.hf_tokens else 1
        
        print(f"[FLUX] 🚀 Параллельная генерация: {len(prompts)} изображений, {actual_workers} потоков")
        
        # Результаты с сохранением порядка
        results = [None] * len(prompts)
        completed = 0
        lock = threading.Lock()
        
        def generate_one(args):
            nonlocal completed
            index, prompt = args
            filename = f"{base_filename}_{index+1:03d}"
            
            # for_parallel=True чтобы токены распределялись между потоками
            result = self.generate(prompt, filename, enhance_prompt=False, for_parallel=True)
            
            with lock:
                completed += 1
                if on_progress:
                    on_progress(completed, len(prompts), result)
            
            return index, result
        
        # Запускаем параллельно
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            futures = {executor.submit(generate_one, (i, p)): i for i, p in enumerate(prompts)}
            
            for future in as_completed(futures):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    index = futures[future]
                    results[index] = FluxResult(success=False, error=str(e))
                    print(f"[FLUX] ❌ Ошибка генерации #{index+1}: {e}")
        
        # Статистика
        success_count = sum(1 for r in results if r and r.success)
        total_time = sum(r.generation_time for r in results if r and r.success)
        
        print(f"[FLUX] ✅ Готово: {success_count}/{len(prompts)} за {total_time:.1f}с")
        
        return results
    
    def get_stats(self) -> dict:
        """Статистика"""
        avg_time = self.stats["total_time"] / max(self.stats["generated"], 1)
        return {
            **self.stats,
            "avg_time": round(avg_time, 2),
            "tokens_count": len(self.hf_tokens),
            "model": "FLUX.1-dev" if self.use_dev else "FLUX.1-schnell"
        }
    
    def get_token_status(self) -> dict:
        """
        Получить статус всех токенов
        
        Returns:
            dict с информацией о доступных и заблокированных токенах
        """
        now = time.time()
        available = []
        in_cooldown = []
        
        for token in self.hf_tokens:
            cooldown_until = self._token_cooldowns.get(token, 0)
            token_short = f"...{token[-8:]}"
            
            if now >= cooldown_until:
                available.append(token_short)
            else:
                remaining = cooldown_until - now
                mins = int(remaining / 60)
                in_cooldown.append({
                    "token": token_short,
                    "remaining_min": mins,
                    "available_at": time.strftime("%H:%M", time.localtime(cooldown_until))
                })
        
        return {
            "total": len(self.hf_tokens),
            "available": len(available),
            "in_cooldown": len(in_cooldown),
            "available_tokens": available[:5],  # Показываем первые 5
            "cooldown_details": in_cooldown[:10],  # Показываем первые 10
            "next_available": min([c["remaining_min"] for c in in_cooldown]) if in_cooldown else 0
        }
    
    def clear_cooldowns(self):
        """Очистить все cooldowns (для тестирования)"""
        self._token_cooldowns = {}
        self._save_cooldowns()
        print(f"[FLUX] Все cooldowns очищены. Доступно {len(self.hf_tokens)} токенов")


# === Глобальный экземпляр ===

_flux_generator: Optional[FluxGenerator] = None


def get_flux_generator() -> FluxGenerator:
    """Получение глобального экземпляра с токенами из конфига"""
    global _flux_generator
    if _flux_generator is None:
        # Загружаем токены из конфига
        try:
            from config import config
            tokens = getattr(config.api, 'huggingface_tokens', [])
        except:
            tokens = []
        
        # Также проверяем переменную окружения
        env_tokens = os.environ.get("HUGGINGFACE_TOKENS", "")
        if env_tokens:
            tokens.extend([t.strip() for t in env_tokens.split(",") if t.strip()])
        
        _flux_generator = FluxGenerator(hf_tokens=tokens)
    
    return _flux_generator


def generate_image(prompt: str, filename: str = "image") -> FluxResult:
    """Быстрая генерация"""
    return get_flux_generator().generate(prompt, filename)


def generate_thumbnail(prompt: str, filename: str = "thumbnail") -> FluxResult:
    """Быстрая генерация превью"""
    return get_flux_generator().generate_thumbnail(prompt, filename)
