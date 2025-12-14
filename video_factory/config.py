"""
Конфигурация приложения
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List


# Пути
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
PROFILES_DIR = DATA_DIR / "channel_profiles"
OUTPUT_DIR = APP_DIR / "output"
QUEUE_DIR = APP_DIR / "queue"
CONFIG_FILE = DATA_DIR / "config.json"
ENV_FILE = APP_DIR / ".env"


def load_env():
    """Загрузка переменных из .env файла"""
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"\''))


# Загружаем .env при импорте
load_env()


@dataclass
class APIConfig:
    """Настройки API"""
    groq_key: str = ""  # Для обратной совместимости
    groq_keys: List[str] = field(default_factory=list)  # Несколько ключей с ротацией!
    youtube_keys: List[str] = field(default_factory=list)  # Несколько ключей
    elevenlabs_keys: List[str] = field(default_factory=list)  # Несколько ключей
    groq_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    
    # AI генераторы превью (thumbnails) — автоматическая ротация
    clipdrop_keys: List[str] = field(default_factory=list)   # Clipdrop — 100 генераций/день БЕСПЛАТНО!
    together_keys: List[str] = field(default_factory=list)   # Together AI (Flux) — $25 бесплатно
    fal_keys: List[str] = field(default_factory=list)        # FAL AI (Flux) — $10 бесплатно
    replicate_keys: List[str] = field(default_factory=list)  # Replicate — бесплатные кредиты
    segmind_keys: List[str] = field(default_factory=list)    # Segmind — 100 кредитов/день БЕСПЛАТНО!
    fireworks_keys: List[str] = field(default_factory=list)  # Fireworks AI — $1 бесплатно
    stability_keys: List[str] = field(default_factory=list)  # Stability AI — 25 кредитов
    novita_keys: List[str] = field(default_factory=list)     # Novita AI — $0.5 бесплатно
    
    # Hugging Face (FLUX генерация)
    huggingface_tokens: List[str] = field(default_factory=list)  # Токены для ротации
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # Индексы для ротации
    _youtube_index: int = 0
    _elevenlabs_index: int = 0
    
    @property
    def youtube_key(self) -> str:
        """Текущий YouTube ключ"""
        if self.youtube_keys:
            return self.youtube_keys[self._youtube_index % len(self.youtube_keys)]
        return ""
    
    @property
    def elevenlabs_key(self) -> str:
        """Текущий ElevenLabs ключ"""
        if self.elevenlabs_keys:
            return self.elevenlabs_keys[self._elevenlabs_index % len(self.elevenlabs_keys)]
        return ""
    
    def rotate_youtube_key(self):
        """Переключить на следующий YouTube ключ"""
        if self.youtube_keys:
            self._youtube_index = (self._youtube_index + 1) % len(self.youtube_keys)
    
    def rotate_elevenlabs_key(self):
        """Переключить на следующий ElevenLabs ключ"""
        if self.elevenlabs_keys:
            self._elevenlabs_index = (self._elevenlabs_index + 1) % len(self.elevenlabs_keys)
    
    @property
    def leonardo_key(self) -> str:
        """Текущий Leonardo ключ"""
        if self.leonardo_keys:
            return self.leonardo_keys[self._leonardo_index % len(self.leonardo_keys)]
        return ""
    
    def rotate_leonardo_key(self):
        """Переключить на следующий Leonardo ключ"""
        if self.leonardo_keys:
            self._leonardo_index = (self._leonardo_index + 1) % len(self.leonardo_keys)
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Загрузка из переменных окружения"""
        # YouTube ключи (через запятую)
        yt_keys_str = os.environ.get("YOUTUBE_API_KEYS", os.environ.get("YOUTUBE_API_KEY", ""))
        yt_keys = [k.strip() for k in yt_keys_str.split(",") if k.strip()]
        
        # ElevenLabs ключи (через запятую)
        el_keys_str = os.environ.get("ELEVENLABS_API_KEYS", os.environ.get("ELEVENLABS_API_KEY", ""))
        el_keys = [k.strip() for k in el_keys_str.split(",") if k.strip()]
        
        # AI генераторы превью
        def parse_keys(env_var: str) -> List[str]:
            val = os.environ.get(env_var, "")
            return [k.strip() for k in val.split(",") if k.strip()]
        
        # Groq ключи (через запятую) — с ротацией при rate limit
        groq_keys_str = os.environ.get("GROQ_API_KEYS", os.environ.get("GROQ_API_KEY", ""))
        groq_keys = [k.strip() for k in groq_keys_str.split(",") if k.strip()]
        
        return cls(
            groq_key=groq_keys[0] if groq_keys else "",  # Для обратной совместимости
            groq_keys=groq_keys,
            youtube_keys=yt_keys,
            elevenlabs_keys=el_keys,
            groq_model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=float(os.environ.get("GROQ_TEMPERATURE", "0.7")),
            clipdrop_keys=parse_keys("CLIPDROP_API_KEYS"),
            together_keys=parse_keys("TOGETHER_API_KEYS"),
            fal_keys=parse_keys("FAL_API_KEYS"),
            replicate_keys=parse_keys("REPLICATE_API_KEYS"),
            segmind_keys=parse_keys("SEGMIND_API_KEYS"),
            fireworks_keys=parse_keys("FIREWORKS_API_KEYS"),
            stability_keys=parse_keys("STABILITY_API_KEYS"),
            novita_keys=parse_keys("NOVITA_API_KEYS"),
            huggingface_tokens=parse_keys("HUGGINGFACE_TOKENS"),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", "")
        )


@dataclass
class PathsConfig:
    """Пути к программам"""
    chrome_path: str = ""
    ffmpeg_path: str = "ffmpeg"
    output_path: str = str(OUTPUT_DIR)


@dataclass
class VideoConfig:
    """Настройки видео"""
    resolution: str = "1920x1080"
    fps: int = 30
    bitrate: str = "12M"


@dataclass
class WhiskConfig:
    """Настройки Whisk"""
    headless: bool = False
    timeout: int = 120


@dataclass
class AppConfig:
    """Главная конфигурация"""
    api: APIConfig = None
    paths: PathsConfig = None
    video: VideoConfig = None
    whisk: WhiskConfig = None
    language: str = "ru"
    
    def __post_init__(self):
        if self.api is None:
            self.api = APIConfig()
        if self.paths is None:
            self.paths = PathsConfig()
        if self.video is None:
            self.video = VideoConfig()
        if self.whisk is None:
            self.whisk = WhiskConfig()
    
    def save(self):
        """Сохранение конфигурации"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "api": {
                "groq_key": self.api.groq_key,
                "groq_keys": self.api.groq_keys,  # Сохраняем groq_keys!
                "youtube_keys": self.api.youtube_keys,
                "elevenlabs_keys": self.api.elevenlabs_keys,
                "groq_model": self.api.groq_model,
                "temperature": self.api.temperature,
                "huggingface_tokens": self.api.huggingface_tokens,
                "telegram_bot_token": self.api.telegram_bot_token,
                "telegram_chat_id": self.api.telegram_chat_id,
            },
            "paths": asdict(self.paths),
            "video": asdict(self.video),
            "whisk": asdict(self.whisk),
            "language": self.language
        }
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls) -> "AppConfig":
        """Загрузка конфигурации"""
        
        # Сначала из переменных окружения
        env_api = APIConfig.from_env()
        has_env_keys = bool(env_api.groq_key or env_api.groq_keys or env_api.youtube_keys or env_api.elevenlabs_keys)
        
        # Если есть config.json — загружаем
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                api_data = data.get("api", {})
                config = cls(
                    api=APIConfig(
                        groq_key=api_data.get("groq_key", ""),
                        groq_keys=api_data.get("groq_keys", []),  # Загружаем groq_keys!
                        youtube_keys=api_data.get("youtube_keys", []),
                        elevenlabs_keys=api_data.get("elevenlabs_keys", []),
                        groq_model=api_data.get("groq_model", "llama-3.3-70b-versatile"),
                        temperature=api_data.get("temperature", 0.7),
                        huggingface_tokens=api_data.get("huggingface_tokens", []),
                        together_keys=api_data.get("together_keys", []),
                        stability_keys=api_data.get("stability_keys", []),
                        replicate_keys=api_data.get("replicate_keys", []),
                        telegram_bot_token=api_data.get("telegram_bot_token", ""),
                        telegram_chat_id=api_data.get("telegram_chat_id", ""),
                    ),
                    paths=PathsConfig(**data.get("paths", {})),
                    video=VideoConfig(**data.get("video", {})),
                    whisk=WhiskConfig(**data.get("whisk", {})),
                    language=data.get("language", "ru")
                )
                
                # Переменные окружения имеют приоритет
                if has_env_keys:
                    if env_api.groq_key:
                        config.api.groq_key = env_api.groq_key
                    if env_api.groq_keys:  # Groq ключи из .env!
                        config.api.groq_keys = env_api.groq_keys
                    if env_api.youtube_keys:
                        config.api.youtube_keys = env_api.youtube_keys
                    if env_api.elevenlabs_keys:
                        config.api.elevenlabs_keys = env_api.elevenlabs_keys
                    # AI генераторы превью
                    if env_api.clipdrop_keys:
                        config.api.clipdrop_keys = env_api.clipdrop_keys
                    if env_api.together_keys:
                        config.api.together_keys = env_api.together_keys
                    if env_api.fal_keys:
                        config.api.fal_keys = env_api.fal_keys
                    if env_api.replicate_keys:
                        config.api.replicate_keys = env_api.replicate_keys
                    if env_api.segmind_keys:
                        config.api.segmind_keys = env_api.segmind_keys
                    if env_api.fireworks_keys:
                        config.api.fireworks_keys = env_api.fireworks_keys
                    if env_api.stability_keys:
                        config.api.stability_keys = env_api.stability_keys
                    if env_api.novita_keys:
                        config.api.novita_keys = env_api.novita_keys
                    if env_api.huggingface_tokens:
                        config.api.huggingface_tokens = env_api.huggingface_tokens
                    # Telegram
                    if env_api.telegram_bot_token:
                        config.api.telegram_bot_token = env_api.telegram_bot_token
                    if env_api.telegram_chat_id:
                        config.api.telegram_chat_id = env_api.telegram_chat_id
                
                return config
                
            except Exception as e:
                print(f"Ошибка загрузки конфига: {e}")
        
        # Создаём новый конфиг — используем ключи из .env
        config = cls()
        config.api = env_api  # Всегда используем env_api для нового конфига
        
        config.save()
        return config


# Глобальный конфиг
config = AppConfig.load()


# Вспомогательные функции
def get_api_status() -> dict:
    """Статус API ключей"""
    return {
        "groq": "✅" if config.api.groq_key else "❌",
        "youtube": f"✅ ({len(config.api.youtube_keys)} ключей)" if config.api.youtube_keys else "❌",
        "elevenlabs": f"✅ ({len(config.api.elevenlabs_keys)} ключей)" if config.api.elevenlabs_keys else "❌",
        "leonardo": f"✅ ({len(config.api.leonardo_keys)} ключей)" if config.api.leonardo_keys else "❌",
        "telegram": "✅" if config.api.telegram_bot_token else "❌",
    }


def print_config_status():
    """Вывод статуса конфигурации"""
    status = get_api_status()
    print("=== Video Factory Config ===")
    print(f"Groq API: {status['groq']}")
    print(f"YouTube API: {status['youtube']}")
    print(f"ElevenLabs API: {status['elevenlabs']}")
    print(f"Output: {config.paths.output_path}")
