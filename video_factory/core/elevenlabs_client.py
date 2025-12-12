"""
Клиент ElevenLabs для озвучки
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import requests


@dataclass
class Voice:
    """Информация о голосе"""
    voice_id: str
    name: str
    category: str
    description: str
    preview_url: str
    labels: Dict[str, str]


class ElevenLabsClient:
    """Клиент для работы с ElevenLabs API с ротацией ключей"""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_keys: list = None, api_key: str = None):
        """
        api_keys: список ключей для ротации
        api_key: один ключ (для обратной совместимости)
        """
        if api_keys:
            self.api_keys = [k for k in api_keys if k]
        elif api_key:
            self.api_keys = [api_key]
        else:
            self.api_keys = []
        
        self.current_key_index = 0
        self._update_headers()
    
    def _update_headers(self):
        """Обновление заголовков с текущим ключом"""
        current_key = self.api_keys[self.current_key_index] if self.api_keys else ""
        self.headers = {
            "xi-api-key": current_key,
            "Content-Type": "application/json"
        }
    
    def rotate_key(self):
        """Переключение на следующий ключ"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._update_headers()
            print(f"Переключение на ElevenLabs ключ #{self.current_key_index + 1}")
    
    @property
    def api_key(self) -> str:
        """Текущий ключ"""
        return self.api_keys[self.current_key_index] if self.api_keys else ""
    
    @property
    def keys_count(self) -> int:
        """Количество ключей"""
        return len(self.api_keys)
    
    def get_voices(self) -> List[Voice]:
        """Получение списка доступных голосов"""
        response = requests.get(
            f"{self.BASE_URL}/voices",
            headers=self.headers
        )
        response.raise_for_status()
        
        voices = []
        for v in response.json().get('voices', []):
            voices.append(Voice(
                voice_id=v['voice_id'],
                name=v['name'],
                category=v.get('category', 'unknown'),
                description=v.get('description', ''),
                preview_url=v.get('preview_url', ''),
                labels=v.get('labels', {})
            ))
        
        return voices
    
    def get_voice_by_name(self, name: str) -> Optional[Voice]:
        """Поиск голоса по имени"""
        voices = self.get_voices()
        for voice in voices:
            if voice.name.lower() == name.lower():
                return voice
        return None
    
    @staticmethod
    def optimize_text_for_speech(text: str) -> str:
        """
        Оптимизация текста для озвучки:
        - Убирает лишние паузы
        - Нормализует пунктуацию
        - Убирает повторяющиеся пробелы
        - Делает текст более плавным для чтения
        """
        import re
        
        # Убираем множественные переносы строк (лишние паузы)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Убираем множественные пробелы
        text = re.sub(r' {2,}', ' ', text)
        
        # Убираем пробелы перед знаками препинания
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Убираем множественные точки (кроме троеточия)
        text = re.sub(r'\.{4,}', '...', text)
        
        # Нормализуем троеточие (не должно создавать длинных пауз)
        text = re.sub(r'\.\.\.+', '...', text)
        
        # Убираем пустые скобки и кавычки
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'"\s*"', '', text)
        
        # Убираем таймкоды типа [0:00] или [ГЛАВА]
        text = re.sub(r'\[[\d:]+\]', '', text)
        text = re.sub(r'\[ГЛАВА[^\]]*\]', '', text)
        text = re.sub(r'\[HOOK[^\]]*\]', '', text)
        text = re.sub(r'\[КУЛЬМИНАЦИЯ\]', '', text)
        text = re.sub(r'\[ЗАКЛЮЧЕНИЕ\]', '', text)
        
        # Убираем лишние тире в начале строк
        text = re.sub(r'\n\s*[-–—]\s*', '\n', text)
        
        # Заменяем длинные тире на короткие паузы
        text = re.sub(r'\s*[-–—]{2,}\s*', ' — ', text)
        
        # Убираем пустые строки в начале и конце
        text = text.strip()
        
        # Финальная очистка множественных пробелов
        text = re.sub(r' {2,}', ' ', text)
        
        return text
    
    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        optimize_text: bool = True,
        language: str = 'ru'
    ) -> Path:
        """Генерация озвучки с автоматической ротацией ключей"""
        
        # Нормализуем текст (даты, числа, аббревиатуры -> слова)
        from core.text_normalizer import normalize_text
        text = normalize_text(text, language)
        
        # Оптимизируем текст для плавной озвучки
        if optimize_text:
            text = self.optimize_text_for_speech(text)
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost
            }
        }
        
        # Пробуем все ключи
        last_error = None
        for attempt in range(len(self.api_keys)):
            try:
                response = requests.post(
                    f"{self.BASE_URL}/text-to-speech/{voice_id}",
                    headers=self.headers,
                    json=data
                )
                
                # Если лимит исчерпан — переключаем ключ
                if response.status_code == 401 or "quota" in response.text.lower():
                    print(f"Ключ #{self.current_key_index + 1} исчерпан, переключаю...")
                    self.rotate_key()
                    continue
                
                response.raise_for_status()
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                return output_path
                
            except Exception as e:
                last_error = e
                self.rotate_key()
        
        raise Exception(f"Все ключи исчерпаны. Последняя ошибка: {last_error}")
    
    def text_to_speech_stream(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> Path:
        """Генерация озвучки с потоковой передачей (для длинных текстов)"""
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/text-to-speech/{voice_id}/stream",
            headers=self.headers,
            json=data,
            stream=True
        )
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        return output_path
    
    def generate_full_voiceover(
        self,
        script: str,
        voice_id: str,
        output_dir: Path,
        chunk_size: int = 4000
    ) -> List[Path]:
        """Генерация озвучки для полного сценария (разбивка на части)"""
        
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_files = []
        
        # Разбиваем на части по параграфам
        paragraphs = script.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            # Пропускаем таймкоды и заголовки глав
            if para.strip().startswith('[') and para.strip().endswith(']'):
                continue
            
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk.strip():
                    # Генерируем аудио для текущего чанка
                    output_path = output_dir / f"chunk_{chunk_index:03d}.mp3"
                    self.text_to_speech(current_chunk.strip(), voice_id, output_path)
                    audio_files.append(output_path)
                    chunk_index += 1
                current_chunk = para + "\n\n"
            else:
                current_chunk += para + "\n\n"
        
        # Последний чанк
        if current_chunk.strip():
            output_path = output_dir / f"chunk_{chunk_index:03d}.mp3"
            self.text_to_speech(current_chunk.strip(), voice_id, output_path)
            audio_files.append(output_path)
        
        return audio_files
    
    def generate_voiceover_parallel(
        self,
        script: str,
        voice_id: str,
        output_dir: Path,
        max_workers: int = 3,
        language: str = 'ru'
    ) -> Path:
        """
        ПАРАЛЛЕЛЬНАЯ генерация озвучки
        
        Разбивает текст на 3 части и генерирует параллельно,
        используя разные API ключи. Затем склеивает в один файл.
        
        С 3 ключами ElevenLabs — в 3 раза быстрее!
        
        Args:
            script: Полный текст сценария
            voice_id: ID голоса
            output_dir: Папка для сохранения
            max_workers: Количество параллельных потоков (по числу ключей)
            language: Язык для нормализации текста
        
        Returns:
            Path к финальному аудио файлу
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Нормализуем текст
        from core.text_normalizer import normalize_text
        script = normalize_text(script, language)
        script = self.optimize_text_for_speech(script)
        
        # Разбиваем на части по параграфам (сохраняя целостность предложений)
        paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
        paragraphs = [p for p in paragraphs if not (p.startswith('[') and p.endswith(']'))]
        
        # Определяем количество частей (по числу ключей, но не больше 3)
        num_parts = min(max_workers, len(self.api_keys), 3)
        if num_parts < 2:
            # Если только 1 ключ — обычная генерация
            output_path = output_dir / "voiceover.mp3"
            return self.text_to_speech(script, voice_id, output_path, language=language)
        
        # Делим параграфы на части
        part_size = len(paragraphs) // num_parts
        parts = []
        for i in range(num_parts):
            start = i * part_size
            end = start + part_size if i < num_parts - 1 else len(paragraphs)
            part_text = '\n\n'.join(paragraphs[start:end])
            parts.append((i, part_text))
        
        total_chars = sum(len(p[1]) for p in parts)
        print(f"[ElevenLabs] 🚀 Параллельная озвучка: {num_parts} частей, {total_chars} символов")
        
        # Генерируем параллельно
        audio_parts = [None] * num_parts
        lock = threading.Lock()
        completed = [0]  # Для отслеживания прогресса
        
        def generate_part(args):
            part_idx, text = args
            
            # Используем разные ключи для разных частей
            with lock:
                original_idx = self.current_key_index
                self.current_key_index = part_idx % len(self.api_keys)
                self._update_headers()
            
            try:
                part_path = output_dir / f"part_{part_idx:02d}.mp3"
                
                data = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                }
                
                # Таймаут 180 сек на часть (3 минуты)
                print(f"  ⏳ Генерация части {part_idx+1}... ({len(text)} символов)")
                response = requests.post(
                    f"{self.BASE_URL}/text-to-speech/{voice_id}",
                    headers=self.headers,
                    json=data,
                    timeout=180
                )
                response.raise_for_status()
                
                with open(part_path, 'wb') as f:
                    f.write(response.content)
                
                with lock:
                    completed[0] += 1
                print(f"  ✅ Часть {part_idx+1}/{num_parts} готова ({completed[0]}/{num_parts} завершено)")
                return part_idx, part_path
                
            finally:
                with lock:
                    self.current_key_index = original_idx
                    self._update_headers()
        
        with ThreadPoolExecutor(max_workers=num_parts) as executor:
            futures = {executor.submit(generate_part, p): p[0] for p in parts}
            
            for future in as_completed(futures):
                try:
                    idx, path = future.result()
                    audio_parts[idx] = path
                except Exception as e:
                    print(f"[ElevenLabs] ❌ Ошибка части: {e}")
        
        # Склеиваем части
        valid_parts = [p for p in audio_parts if p and p.exists()]
        
        if len(valid_parts) == 1:
            # Только одна часть — просто переименовываем
            final_path = output_dir / "voiceover.mp3"
            valid_parts[0].rename(final_path)
            return final_path
        
        if len(valid_parts) > 1:
            final_path = self._merge_audio_files(valid_parts, output_dir / "voiceover.mp3")
            # Удаляем временные файлы
            for p in valid_parts:
                try:
                    p.unlink()
                except:
                    pass
            return final_path
        
        raise Exception("Не удалось сгенерировать озвучку")
    
    def _merge_audio_files(self, audio_files: List[Path], output_path: Path) -> Path:
        """Склеивание аудио файлов в один"""
        try:
            from pydub import AudioSegment
            
            combined = AudioSegment.empty()
            for audio_file in audio_files:
                segment = AudioSegment.from_mp3(str(audio_file))
                combined += segment
            
            combined.export(str(output_path), format="mp3")
            return output_path
            
        except ImportError:
            # Если pydub не установлен — используем ffmpeg напрямую
            import subprocess
            
            # Создаём файл со списком
            list_file = output_path.parent / "concat_list.txt"
            with open(list_file, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file.absolute()}'\n")
            
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', str(list_file), '-c', 'copy', str(output_path)
            ], capture_output=True)
            
            list_file.unlink()
            return output_path
    
    def get_user_info(self) -> Dict[str, Any]:
        """Информация о пользователе и лимитах"""
        response = requests.get(
            f"{self.BASE_URL}/user",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_character_count(self) -> Dict[str, int]:
        """Получение использованных символов"""
        user_info = self.get_user_info()
        subscription = user_info.get('subscription', {})
        
        return {
            'used': subscription.get('character_count', 0),
            'limit': subscription.get('character_limit', 0),
            'remaining': subscription.get('character_limit', 0) - subscription.get('character_count', 0)
        }
    
    @staticmethod
    def recommend_voice(style: str, tone: str, gender: str = "male") -> str:
        """Рекомендация голоса на основе стиля"""
        
        recommendations = {
            ("документальный", "серьёзный", "male"): "Adam",
            ("документальный", "серьёзный", "female"): "Rachel",
            ("документальный", "драматичный", "male"): "Arnold",
            ("развлекательный", "лёгкий", "male"): "Josh",
            ("развлекательный", "лёгкий", "female"): "Bella",
            ("образовательный", "спокойный", "male"): "Antoni",
            ("образовательный", "спокойный", "female"): "Elli",
            ("драматический", "напряжённый", "male"): "Arnold",
        }
        
        key = (style.lower(), tone.lower(), gender.lower())
        return recommendations.get(key, "Adam")
    
    def match_voice_to_competitor(self, competitor_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подбор голоса из библиотеки ElevenLabs на основе анализа конкурента
        
        Args:
            competitor_analysis: Результат анализа голоса конкурента
                {
                    "gender": "male/female",
                    "age": "young/middle/old",
                    "tone": "serious/casual/dramatic",
                    "speed": "slow/medium/fast",
                    "emotion": "calm/energetic/dramatic"
                }
        
        Returns:
            {
                "voice_id": "...",
                "voice_name": "...",
                "match_score": 85,
                "reason": "почему этот голос подходит"
            }
        """
        # Библиотека голосов с характеристиками
        voice_profiles = {
            "pNInz6obpgDQGcFmaJgB": {  # Adam
                "name": "Adam",
                "gender": "male",
                "age": "middle",
                "tone": "serious",
                "speed": "medium",
                "emotion": "calm",
                "best_for": ["документальный", "история", "наука"]
            },
            "nPczCjzI2devNBz1zQrb": {  # Brian
                "name": "Brian",
                "gender": "male",
                "age": "middle",
                "tone": "serious",
                "speed": "medium",
                "emotion": "dramatic",
                "best_for": ["нарратив", "история", "военная тематика"]
            },
            "2EiwWnXFnvU5JabPnv8n": {  # Clyde
                "name": "Clyde",
                "gender": "male",
                "age": "old",
                "tone": "serious",
                "speed": "slow",
                "emotion": "dramatic",
                "best_for": ["военная история", "драма", "эпос"]
            },
            "JBFqnCBsd6RMkjVDRZzb": {  # George
                "name": "George",
                "gender": "male",
                "age": "middle",
                "tone": "casual",
                "speed": "medium",
                "emotion": "calm",
                "best_for": ["образование", "объяснения", "туториалы"]
            },
            "onwK4e9ZLuTAKqWW03F9": {  # Daniel
                "name": "Daniel",
                "gender": "male",
                "age": "young",
                "tone": "serious",
                "speed": "medium",
                "emotion": "calm",
                "best_for": ["новости", "документальный", "британский стиль"]
            },
            "21m00Tcm4TlvDq8ikWAM": {  # Rachel
                "name": "Rachel",
                "gender": "female",
                "age": "middle",
                "tone": "serious",
                "speed": "medium",
                "emotion": "calm",
                "best_for": ["документальный", "наука", "спокойный нарратив"]
            },
            "XrExE9yKIg1WjnnlVkGX": {  # Matilda
                "name": "Matilda",
                "gender": "female",
                "age": "middle",
                "tone": "serious",
                "speed": "medium",
                "emotion": "dramatic",
                "best_for": ["профессиональный", "бизнес", "презентации"]
            },
            "EXAVITQu4vr4xnSDxMaL": {  # Bella
                "name": "Bella",
                "gender": "female",
                "age": "young",
                "tone": "casual",
                "speed": "fast",
                "emotion": "energetic",
                "best_for": ["развлечения", "лайфстайл", "молодёжный контент"]
            },
        }
        
        # Подсчёт совпадений
        best_match = None
        best_score = 0
        
        for voice_id, profile in voice_profiles.items():
            score = 0
            
            # Пол (важнее всего)
            if profile["gender"] == competitor_analysis.get("gender", "male"):
                score += 30
            
            # Возраст
            if profile["age"] == competitor_analysis.get("age", "middle"):
                score += 20
            
            # Тон
            if profile["tone"] == competitor_analysis.get("tone", "serious"):
                score += 20
            
            # Скорость
            if profile["speed"] == competitor_analysis.get("speed", "medium"):
                score += 15
            
            # Эмоциональность
            if profile["emotion"] == competitor_analysis.get("emotion", "calm"):
                score += 15
            
            if score > best_score:
                best_score = score
                best_match = (voice_id, profile)
        
        if best_match:
            voice_id, profile = best_match
            return {
                "voice_id": voice_id,
                "voice_name": profile["name"],
                "match_score": best_score,
                "reason": f"Подходит для: {', '.join(profile['best_for'])}",
                "profile": profile
            }
        
        # Дефолт — Brian для военной тематики
        return {
            "voice_id": "nPczCjzI2devNBz1zQrb",
            "voice_name": "Brian",
            "match_score": 50,
            "reason": "Универсальный голос для нарратива"
        }
    
    # === ГОЛОСОВОЕ КЛОНИРОВАНИЕ ===
    
    def clone_voice(self, name: str, audio_files: List[Path], 
                    description: str = "") -> Optional[str]:
        """
        Клонирование голоса из аудио образцов
        
        Args:
            name: Название голоса (будет отображаться в списке)
            audio_files: Список путей к аудио файлам (MP3/WAV, 1-25 файлов)
            description: Описание голоса
        
        Returns:
            voice_id клонированного голоса или None при ошибке
        
        Требования к образцам:
        - Минимум 1 файл, рекомендуется 3-5
        - Чистая речь без фоновой музыки/шума
        - Длительность каждого: 30 сек - 3 мин
        - Форматы: MP3, WAV, M4A
        - Общая длительность: 1-30 минут
        """
        if not audio_files:
            raise ValueError("Нужен минимум 1 аудио файл для клонирования")
        
        # Проверяем файлы
        valid_files = []
        for f in audio_files:
            path = Path(f)
            if path.exists() and path.suffix.lower() in ['.mp3', '.wav', '.m4a']:
                valid_files.append(path)
        
        if not valid_files:
            raise ValueError("Не найдено валидных аудио файлов (MP3/WAV/M4A)")
        
        # Пробуем все ключи
        last_error = None
        for attempt in range(len(self.api_keys)):
            try:
                # Подготавливаем файлы для загрузки
                files = []
                for i, audio_path in enumerate(valid_files):
                    files.append(
                        ('files', (audio_path.name, open(audio_path, 'rb'), 'audio/mpeg'))
                    )
                
                data = {
                    'name': name,
                    'description': description or f"Клонированный голос: {name}"
                }
                
                # Отправляем запрос (без Content-Type, requests сам поставит multipart)
                headers = {"xi-api-key": self.api_key}
                
                response = requests.post(
                    f"{self.BASE_URL}/voices/add",
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=120
                )
                
                # Закрываем файлы
                for _, (_, f, _) in files:
                    f.close()
                
                if response.status_code == 401 or "quota" in response.text.lower():
                    self.rotate_key()
                    continue
                
                response.raise_for_status()
                
                result = response.json()
                voice_id = result.get('voice_id')
                
                print(f"✅ Голос '{name}' успешно клонирован! ID: {voice_id}")
                return voice_id
                
            except Exception as e:
                last_error = e
                # Закрываем файлы при ошибке
                for item in files:
                    try:
                        item[1][1].close()
                    except:
                        pass
                self.rotate_key()
        
        raise Exception(f"Не удалось клонировать голос. Последняя ошибка: {last_error}")
    
    def get_cloned_voices(self) -> List[Voice]:
        """Получение списка клонированных голосов"""
        all_voices = self.get_voices()
        return [v for v in all_voices if v.category == 'cloned']
    
    def delete_voice(self, voice_id: str) -> bool:
        """Удаление клонированного голоса"""
        try:
            response = requests.delete(
                f"{self.BASE_URL}/voices/{voice_id}",
                headers=self.headers,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка удаления голоса: {e}")
            return False
    
    def edit_voice(self, voice_id: str, name: str = None, 
                   description: str = None) -> bool:
        """Редактирование информации о голосе"""
        try:
            data = {}
            if name:
                data['name'] = name
            if description:
                data['description'] = description
            
            if not data:
                return True
            
            response = requests.post(
                f"{self.BASE_URL}/voices/{voice_id}/edit",
                headers=self.headers,
                json=data,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка редактирования голоса: {e}")
            return False
