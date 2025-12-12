"""
Telegram уведомления — узнаёшь когда очередь готова
"""

import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class NotificationConfig:
    """Настройки уведомлений"""
    bot_token: str
    chat_id: str
    enabled: bool = True
    notify_on_complete: bool = True      # Когда проект готов
    notify_on_error: bool = True         # При ошибке
    notify_on_queue_done: bool = True    # Когда вся очередь завершена
    send_preview: bool = True            # Отправлять превью картинку


class TelegramNotifier:
    """
    Telegram бот для уведомлений о статусе Video Factory
    
    Как настроить:
    1. Найди @BotFather в Telegram
    2. Отправь /newbot и следуй инструкциям
    3. Получи токен бота (например: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
    4. Найди своего бота и отправь ему /start
    5. Получи свой chat_id через @userinfobot или @getmyid_bot
    6. Введи токен и chat_id в настройках Video Factory
    """
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
    
    def configure(self, bot_token: str, chat_id: str):
        """Настройка бота"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
    
    def test_connection(self) -> tuple[bool, str]:
        """Проверка подключения к боту"""
        if not self.enabled:
            return False, "Бот не настроен. Укажите токен и chat_id"
        
        try:
            # Проверяем токен
            response = requests.get(
                f"{self.BASE_URL}{self.bot_token}/getMe",
                timeout=10
            )
            
            if response.status_code != 200:
                return False, f"Неверный токен бота: {response.text}"
            
            bot_info = response.json()
            if not bot_info.get('ok'):
                return False, f"Ошибка API: {bot_info.get('description', 'Unknown')}"
            
            bot_name = bot_info['result'].get('username', 'Unknown')
            
            # Отправляем тестовое сообщение
            test_result = self.send_message("🤖 Video Factory подключен!\n\nТеперь вы будете получать уведомления о готовности видео.")
            
            if test_result:
                return True, f"✅ Подключено к боту @{bot_name}"
            else:
                return False, f"Бот @{bot_name} найден, но не удалось отправить сообщение. Проверьте chat_id"
                
        except requests.exceptions.Timeout:
            return False, "Таймаут подключения к Telegram"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Отправка текстового сообщения"""
        if not self.enabled:
            return False
        
        try:
            response = requests.post(
                f"{self.BASE_URL}{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=30
            )
            return response.status_code == 200 and response.json().get('ok', False)
        except Exception as e:
            print(f"[Telegram] Ошибка отправки: {e}")
            return False
    
    def send_photo(self, photo_path: Path, caption: str = "") -> bool:
        """Отправка фото с подписью"""
        if not self.enabled:
            return False
        
        if not photo_path.exists():
            return False
        
        try:
            with open(photo_path, 'rb') as photo:
                response = requests.post(
                    f"{self.BASE_URL}{self.bot_token}/sendPhoto",
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "HTML"
                    },
                    files={"photo": photo},
                    timeout=60
                )
            return response.status_code == 200 and response.json().get('ok', False)
        except Exception as e:
            print(f"[Telegram] Ошибка отправки фото: {e}")
            return False
    
    def send_document(self, file_path: Path, caption: str = "") -> bool:
        """Отправка файла"""
        if not self.enabled:
            return False
        
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'rb') as doc:
                response = requests.post(
                    f"{self.BASE_URL}{self.bot_token}/sendDocument",
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "HTML"
                    },
                    files={"document": doc},
                    timeout=120
                )
            return response.status_code == 200 and response.json().get('ok', False)
        except Exception as e:
            print(f"[Telegram] Ошибка отправки файла: {e}")
            return False
    
    # === УВЕДОМЛЕНИЯ О ПРОЕКТАХ ===
    
    def notify_project_ready(self, project_name: str, preview_path: Optional[Path] = None,
                             seo_title: str = "", images_count: int = 0):
        """Уведомление о готовности проекта к проверке"""
        
        message = f"""🎬 <b>Проект готов к проверке!</b>

📌 <b>{project_name}</b>

"""
        if seo_title:
            message += f"📝 Заголовок: {seo_title}\n"
        if images_count:
            message += f"🖼 Изображений: {images_count}\n"
        
        message += "\n✅ Откройте Video Factory для просмотра и рендера"
        
        # Отправляем превью если есть
        if preview_path and preview_path.exists():
            self.send_photo(preview_path, message)
        else:
            self.send_message(message)
    
    def notify_project_error(self, project_name: str, error: str):
        """Уведомление об ошибке"""
        
        message = f"""❌ <b>Ошибка в проекте</b>

📌 <b>{project_name}</b>

⚠️ {error}

Откройте Video Factory для исправления"""
        
        self.send_message(message)
    
    def notify_queue_complete(self, total_projects: int, successful: int, failed: int):
        """Уведомление о завершении очереди"""
        
        status_emoji = "✅" if failed == 0 else "⚠️"
        
        message = f"""{status_emoji} <b>Очередь завершена!</b>

📊 <b>Статистика:</b>
• Всего проектов: {total_projects}
• Успешно: {successful} ✅
• С ошибками: {failed} ❌

🎬 Откройте Video Factory для просмотра результатов"""
        
        self.send_message(message)
    
    def notify_render_complete(self, project_name: str, video_path: Path, 
                               duration_minutes: float = 0):
        """Уведомление о завершении рендера"""
        
        file_size = video_path.stat().st_size / (1024 * 1024) if video_path.exists() else 0
        
        message = f"""🎉 <b>Рендер завершён!</b>

📌 <b>{project_name}</b>

📁 Размер: {file_size:.1f} MB
⏱ Длительность: ~{duration_minutes:.0f} мин

🚀 Видео готово к загрузке на YouTube!"""
        
        self.send_message(message)
    
    def notify_daily_summary(self, projects_created: int, projects_rendered: int,
                             total_duration_hours: float):
        """Ежедневная сводка"""
        
        message = f"""📊 <b>Дневная сводка Video Factory</b>

🎬 Создано проектов: {projects_created}
✅ Отрендерено: {projects_rendered}
⏱ Общая длительность: {total_duration_hours:.1f} ч

Хорошего дня! 🌟"""
        
        self.send_message(message)


# === ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ===

_notifier: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    """Получение глобального экземпляра нотификатора"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


def setup_notifier(bot_token: str, chat_id: str) -> TelegramNotifier:
    """Настройка глобального нотификатора"""
    global _notifier
    _notifier = TelegramNotifier(bot_token, chat_id)
    return _notifier
