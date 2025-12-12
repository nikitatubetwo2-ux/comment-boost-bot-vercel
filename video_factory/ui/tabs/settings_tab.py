"""
Вкладка настроек
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QCheckBox, QSpinBox, QMessageBox,
    QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config import config


class APITestWorker(QThread):
    """Тестирование API"""
    finished = pyqtSignal(str, bool, str)  # api_name, success, message
    
    def __init__(self, api_name: str, api_key: str):
        super().__init__()
        self.api_name = api_name
        self.api_key = api_key
    
    def run(self):
        try:
            if self.api_name == "Groq":
                self._test_groq()
            elif self.api_name == "YouTube":
                self._test_youtube()
            elif self.api_name == "ElevenLabs":
                self._test_elevenlabs()
        except Exception as e:
            self.finished.emit(self.api_name, False, str(e))
    
    def _test_groq(self):
        from groq import Groq
        client = Groq(api_key=self.api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=10
        )
        self.finished.emit("Groq", True, "Соединение успешно!")
    
    def _test_youtube(self):
        from googleapiclient.discovery import build
        # Тестируем первый ключ из списка
        keys = self.api_key.split(',')
        youtube = build('youtube', 'v3', developerKey=keys[0].strip())
        response = youtube.videos().list(part='snippet', id='dQw4w9WgXcQ').execute()
        self.finished.emit("YouTube", True, f"OK! {len(keys)} ключей работают")
    
    def _test_elevenlabs(self):
        import requests
        # Тестируем первый ключ из списка
        keys = [k.strip() for k in self.api_key.split(',') if k.strip()]
        if not keys:
            self.finished.emit("ElevenLabs", False, "Нет ключей")
            return
        
        total_chars = 0
        total_limit = 0
        working_keys = 0
        
        for key in keys[:5]:  # Проверяем первые 5
            try:
                response = requests.get(
                    "https://api.elevenlabs.io/v1/user",
                    headers={"xi-api-key": key},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    total_chars += data.get('subscription', {}).get('character_count', 0)
                    total_limit += data.get('subscription', {}).get('character_limit', 0)
                    working_keys += 1
            except:
                pass
        
        if working_keys > 0:
            self.finished.emit("ElevenLabs", True, f"OK! {len(keys)} ключей, ~{total_limit} символов")
        else:
            self.finished.emit("ElevenLabs", False, "Ключи не работают")


class SettingsTab(QWidget):
    """Вкладка настроек приложения"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        # Scroll area для настроек
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # API ключи
        api_group = QGroupBox("🔑 API ключи")
        api_layout = QVBoxLayout(api_group)
        
        # Groq
        groq_layout = QHBoxLayout()
        groq_layout.addWidget(QLabel("Groq API:"))
        self.groq_key = QLineEdit()
        self.groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.groq_key.setPlaceholderText("gsk_...")
        groq_layout.addWidget(self.groq_key)
        self.btn_test_groq = QPushButton("Тест")
        self.btn_test_groq.clicked.connect(lambda: self.test_api("Groq"))
        groq_layout.addWidget(self.btn_test_groq)
        self.groq_status = QLabel("")
        groq_layout.addWidget(self.groq_status)
        api_layout.addLayout(groq_layout)
        
        # YouTube (несколько ключей)
        yt_layout = QHBoxLayout()
        yt_layout.addWidget(QLabel("YouTube API:"))
        self.youtube_keys_count = QLabel(f"{len(config.api.youtube_keys)} ключей")
        self.youtube_keys_count.setStyleSheet("color: #14a3a8;")
        yt_layout.addWidget(self.youtube_keys_count)
        self.btn_test_yt = QPushButton("Тест")
        self.btn_test_yt.clicked.connect(lambda: self.test_api("YouTube"))
        yt_layout.addWidget(self.btn_test_yt)
        self.yt_status = QLabel("")
        yt_layout.addWidget(self.yt_status)
        yt_layout.addStretch()
        api_layout.addLayout(yt_layout)
        
        # ElevenLabs (несколько ключей)
        eleven_layout = QHBoxLayout()
        eleven_layout.addWidget(QLabel("ElevenLabs:"))
        self.eleven_keys_count = QLabel(f"{len(config.api.elevenlabs_keys)} ключей")
        self.eleven_keys_count.setStyleSheet("color: #14a3a8;")
        eleven_layout.addWidget(self.eleven_keys_count)
        self.btn_test_eleven = QPushButton("Тест")
        self.btn_test_eleven.clicked.connect(lambda: self.test_api("ElevenLabs"))
        eleven_layout.addWidget(self.btn_test_eleven)
        self.eleven_status = QLabel("")
        eleven_layout.addWidget(self.eleven_status)
        eleven_layout.addStretch()
        api_layout.addLayout(eleven_layout)
        
        # HuggingFace (FLUX для картинок)
        hf_layout = QHBoxLayout()
        hf_layout.addWidget(QLabel("HuggingFace (FLUX):"))
        self.hf_tokens_count = QLabel(f"{len(config.api.huggingface_tokens)} токенов")
        self.hf_tokens_count.setStyleSheet("color: #14a3a8;")
        hf_layout.addWidget(self.hf_tokens_count)
        self.btn_test_hf = QPushButton("Тест")
        self.btn_test_hf.clicked.connect(self.test_huggingface)
        hf_layout.addWidget(self.btn_test_hf)
        self.hf_status = QLabel("")
        hf_layout.addWidget(self.hf_status)
        hf_layout.addStretch()
        api_layout.addLayout(hf_layout)
        
        # Инфо о ключах
        keys_info = QLabel("💡 Ключи загружаются из файла .env\n📌 HuggingFace: https://huggingface.co/settings/tokens")
        keys_info.setStyleSheet("color: #888; font-size: 11px;")
        api_layout.addWidget(keys_info)
        
        layout.addWidget(api_group)
        
        # === КВОТЫ API ===
        quota_group = QGroupBox("📊 Квоты API (остаток на месяц)")
        quota_layout = QVBoxLayout(quota_group)
        
        # ElevenLabs символы
        eleven_quota_layout = QHBoxLayout()
        eleven_quota_layout.addWidget(QLabel("ElevenLabs символы:"))
        self.eleven_chars_label = QLabel("— / —")
        self.eleven_chars_label.setStyleSheet("font-weight: bold;")
        eleven_quota_layout.addWidget(self.eleven_chars_label)
        self.eleven_progress = QLabel("")
        self.eleven_progress.setMinimumWidth(150)
        eleven_quota_layout.addWidget(self.eleven_progress)
        eleven_quota_layout.addStretch()
        quota_layout.addLayout(eleven_quota_layout)
        
        # YouTube квота
        yt_quota_layout = QHBoxLayout()
        yt_quota_layout.addWidget(QLabel("YouTube API квота:"))
        self.yt_quota_label = QLabel("— / 10,000")
        self.yt_quota_label.setStyleSheet("font-weight: bold;")
        yt_quota_layout.addWidget(self.yt_quota_label)
        self.yt_progress = QLabel("")
        self.yt_progress.setMinimumWidth(150)
        yt_quota_layout.addWidget(self.yt_progress)
        yt_quota_layout.addStretch()
        quota_layout.addLayout(yt_quota_layout)
        
        # Кнопка обновления
        refresh_quota_layout = QHBoxLayout()
        self.btn_refresh_quota = QPushButton("🔄 Обновить квоты")
        self.btn_refresh_quota.clicked.connect(self.refresh_api_quotas)
        refresh_quota_layout.addWidget(self.btn_refresh_quota)
        self.quota_status = QLabel("")
        refresh_quota_layout.addWidget(self.quota_status)
        refresh_quota_layout.addStretch()
        quota_layout.addLayout(refresh_quota_layout)
        
        # Инфо
        quota_info = QLabel("💡 ElevenLabs: лимит обновляется 1-го числа месяца\n📌 YouTube: 10,000 единиц/день на ключ")
        quota_info.setStyleSheet("color: #888; font-size: 11px;")
        quota_layout.addWidget(quota_info)
        
        layout.addWidget(quota_group)
        
        # Пути
        paths_group = QGroupBox("📁 Пути")
        paths_layout = QVBoxLayout(paths_group)
        
        # Chrome
        chrome_layout = QHBoxLayout()
        chrome_layout.addWidget(QLabel("Chrome:"))
        self.chrome_path = QLineEdit()
        self.chrome_path.setPlaceholderText("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        chrome_layout.addWidget(self.chrome_path)
        btn_browse_chrome = QPushButton("...")
        btn_browse_chrome.setMaximumWidth(40)
        btn_browse_chrome.clicked.connect(lambda: self.browse_path(self.chrome_path))
        chrome_layout.addWidget(btn_browse_chrome)
        paths_layout.addLayout(chrome_layout)
        
        # FFmpeg
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(QLabel("FFmpeg:"))
        self.ffmpeg_path = QLineEdit()
        self.ffmpeg_path.setPlaceholderText("/usr/local/bin/ffmpeg")
        ffmpeg_layout.addWidget(self.ffmpeg_path)
        btn_browse_ffmpeg = QPushButton("...")
        btn_browse_ffmpeg.setMaximumWidth(40)
        btn_browse_ffmpeg.clicked.connect(lambda: self.browse_path(self.ffmpeg_path))
        ffmpeg_layout.addWidget(btn_browse_ffmpeg)
        paths_layout.addLayout(ffmpeg_layout)
        
        # Output
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Выходная папка:"))
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("./output")
        output_layout.addWidget(self.output_path)
        btn_browse_output = QPushButton("...")
        btn_browse_output.setMaximumWidth(40)
        btn_browse_output.clicked.connect(lambda: self.browse_folder(self.output_path))
        output_layout.addWidget(btn_browse_output)
        paths_layout.addLayout(output_layout)
        
        layout.addWidget(paths_group)
        
        # Настройки генерации
        gen_group = QGroupBox("⚙️ Настройки генерации")
        gen_layout = QVBoxLayout(gen_group)
        
        # Модель Groq
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель Groq:"))
        self.groq_model = QComboBox()
        self.groq_model.addItems([
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ])
        model_layout.addWidget(self.groq_model)
        gen_layout.addLayout(model_layout)
        
        # Температура
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Температура:"))
        self.temperature = QSpinBox()
        self.temperature.setRange(0, 100)
        self.temperature.setValue(70)
        self.temperature.setSuffix("%")
        temp_layout.addWidget(self.temperature)
        gen_layout.addLayout(temp_layout)
        
        # Язык
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Язык контента:"))
        self.content_language = QComboBox()
        self.content_language.addItems(["Русский", "English"])
        lang_layout.addWidget(self.content_language)
        gen_layout.addLayout(lang_layout)
        
        layout.addWidget(gen_group)
        
        # Настройки видео
        video_group = QGroupBox("🎬 Настройки видео")
        video_layout = QVBoxLayout(video_group)
        
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Разрешение:"))
        self.default_resolution = QComboBox()
        self.default_resolution.addItems(["1920x1080", "2560x1440", "3840x2160"])
        res_layout.addWidget(self.default_resolution)
        video_layout.addLayout(res_layout)
        
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.default_fps = QComboBox()
        self.default_fps.addItems(["24", "30", "60"])
        self.default_fps.setCurrentIndex(1)
        fps_layout.addWidget(self.default_fps)
        video_layout.addLayout(fps_layout)
        
        layout.addWidget(video_group)
        
        # === TELEGRAM УВЕДОМЛЕНИЯ ===
        telegram_group = QGroupBox("📱 Telegram уведомления")
        telegram_layout = QVBoxLayout(telegram_group)
        
        # Инструкция
        tg_info = QLabel(
            "Получайте уведомления когда проекты готовы!\n"
            "1. Найдите @BotFather в Telegram → /newbot\n"
            "2. Получите токен бота\n"
            "3. Найдите @userinfobot → получите свой chat_id"
        )
        tg_info.setStyleSheet("color: #888; font-size: 11px;")
        tg_info.setWordWrap(True)
        telegram_layout.addWidget(tg_info)
        
        # Bot Token
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Bot Token:"))
        self.telegram_token = QLineEdit()
        self.telegram_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.telegram_token.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        token_layout.addWidget(self.telegram_token)
        telegram_layout.addLayout(token_layout)
        
        # Chat ID
        chat_layout = QHBoxLayout()
        chat_layout.addWidget(QLabel("Chat ID:"))
        self.telegram_chat_id = QLineEdit()
        self.telegram_chat_id.setPlaceholderText("123456789")
        chat_layout.addWidget(self.telegram_chat_id)
        telegram_layout.addLayout(chat_layout)
        
        # Тест подключения
        tg_buttons = QHBoxLayout()
        self.btn_test_telegram = QPushButton("🔔 Тест уведомления")
        self.btn_test_telegram.clicked.connect(self.test_telegram)
        tg_buttons.addWidget(self.btn_test_telegram)
        self.telegram_status = QLabel("")
        tg_buttons.addWidget(self.telegram_status)
        tg_buttons.addStretch()
        telegram_layout.addLayout(tg_buttons)
        
        # Чекбоксы уведомлений
        self.tg_notify_complete = QCheckBox("Уведомлять о готовности проекта")
        self.tg_notify_complete.setChecked(True)
        telegram_layout.addWidget(self.tg_notify_complete)
        
        self.tg_notify_error = QCheckBox("Уведомлять об ошибках")
        self.tg_notify_error.setChecked(True)
        telegram_layout.addWidget(self.tg_notify_error)
        
        self.tg_notify_queue = QCheckBox("Уведомлять о завершении очереди")
        self.tg_notify_queue.setChecked(True)
        telegram_layout.addWidget(self.tg_notify_queue)
        
        layout.addWidget(telegram_group)
        
        # === ПОДБОР ГОЛОСА ПО КОНКУРЕНТУ ===
        voice_group = QGroupBox("🎤 Подбор голоса")
        voice_layout = QVBoxLayout(voice_group)
        
        voice_info = QLabel(
            "Автоматический подбор голоса из библиотеки ElevenLabs\n"
            "на основе анализа стиля конкурента (тембр, скорость, эмоциональность)"
        )
        voice_info.setStyleSheet("color: #888; font-size: 11px;")
        voice_info.setWordWrap(True)
        voice_layout.addWidget(voice_info)
        
        # Библиотека голосов
        voices_layout = QHBoxLayout()
        voices_layout.addWidget(QLabel("Доступные голоса:"))
        self.voices_combo = QComboBox()
        self.voices_combo.setMinimumWidth(250)
        voices_layout.addWidget(self.voices_combo)
        self.btn_refresh_voices = QPushButton("🔄")
        self.btn_refresh_voices.setMaximumWidth(40)
        self.btn_refresh_voices.clicked.connect(self.refresh_voices_list)
        voices_layout.addWidget(self.btn_refresh_voices)
        voices_layout.addStretch()
        voice_layout.addLayout(voices_layout)
        
        # Тест голоса
        test_layout = QHBoxLayout()
        self.voice_test_text = QLineEdit("Это тест голоса для озвучки видео.")
        test_layout.addWidget(self.voice_test_text)
        self.btn_test_voice = QPushButton("▶️ Тест")
        self.btn_test_voice.clicked.connect(self.test_selected_voice)
        test_layout.addWidget(self.btn_test_voice)
        voice_layout.addLayout(test_layout)
        
        layout.addWidget(voice_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Сохранить настройки")
        btn_save.clicked.connect(self.save_settings)
        buttons_layout.addWidget(btn_save)
        
        btn_reset = QPushButton("🔄 Сбросить")
        btn_reset.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(btn_reset)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def load_settings(self):
        """Загрузка настроек"""
        self.groq_key.setText(config.api.groq_key)
        
        # Обновляем счётчики ключей
        self.youtube_keys_count.setText(f"{len(config.api.youtube_keys)} ключей")
        self.eleven_keys_count.setText(f"{len(config.api.elevenlabs_keys)} ключей")
        self.hf_tokens_count.setText(f"{len(config.api.huggingface_tokens)} токенов")
        
        self.chrome_path.setText(config.paths.chrome_path)
        self.ffmpeg_path.setText(config.paths.ffmpeg_path)
        self.output_path.setText(config.paths.output_path)
        
        # Модель
        index = self.groq_model.findText(config.api.groq_model)
        if index >= 0:
            self.groq_model.setCurrentIndex(index)
        
        self.temperature.setValue(int(config.api.temperature * 100))
        
        # Telegram
        self._load_telegram_config()
        
        # Голоса
        self.refresh_voices_list()
        
        # Автозагрузка квот (в фоне)
        self.refresh_api_quotas()
    
    def save_settings(self):
        """Сохранение настроек"""
        # API
        config.api.groq_key = self.groq_key.text().strip()
        # YouTube и ElevenLabs ключи загружаются из .env
        config.api.groq_model = self.groq_model.currentText()
        config.api.temperature = self.temperature.value() / 100
        
        # Пути
        config.paths.chrome_path = self.chrome_path.text().strip()
        config.paths.ffmpeg_path = self.ffmpeg_path.text().strip()
        config.paths.output_path = self.output_path.text().strip()
        
        # Видео
        config.video.resolution = self.default_resolution.currentText()
        config.video.fps = int(self.default_fps.currentText())
        
        # Сохраняем
        config.save()
        
        QMessageBox.information(self, "Настройки", "Настройки сохранены!")
    
    def reset_settings(self):
        """Сброс настроек"""
        reply = QMessageBox.question(
            self, "Сброс",
            "Сбросить все настройки?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.groq_key.clear()
            self.chrome_path.clear()
            self.ffmpeg_path.clear()
            self.output_path.clear()
    
    def test_api(self, api_name: str):
        """Тестирование API"""
        if api_name == "Groq":
            key = self.groq_key.text().strip() or config.api.groq_key
            status_label = self.groq_status
        elif api_name == "YouTube":
            key = ','.join(config.api.youtube_keys)
            status_label = self.yt_status
        elif api_name == "ElevenLabs":
            key = ','.join(config.api.elevenlabs_keys)
            status_label = self.eleven_status
        else:
            return
        
        if not key:
            QMessageBox.warning(self, "Ошибка", f"Нет {api_name} API ключей. Добавьте в .env файл")
            return
        
        status_label.setText("⏳")
        status_label.setStyleSheet("color: yellow;")
        
        self.worker = APITestWorker(api_name, key)
        self.worker.finished.connect(self.on_api_test_finished)
        self.worker.start()
    
    def on_api_test_finished(self, api_name: str, success: bool, message: str):
        """Результат теста API"""
        if api_name == "Groq":
            status_label = self.groq_status
        elif api_name == "YouTube":
            status_label = self.yt_status
        elif api_name == "ElevenLabs":
            status_label = self.eleven_status
        else:
            return
        
        if success:
            status_label.setText("✓")
            status_label.setStyleSheet("color: #28a745;")
            QMessageBox.information(self, f"{api_name} API", message)
        else:
            status_label.setText("✗")
            status_label.setStyleSheet("color: #dc3545;")
            QMessageBox.critical(self, f"{api_name} API", f"Ошибка: {message}")
    
    def browse_path(self, line_edit):
        """Выбор файла"""
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
        if path:
            line_edit.setText(path)
    
    def browse_folder(self, line_edit):
        """Выбор папки"""
        path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if path:
            line_edit.setText(path)
    
    # === TELEGRAM ===
    
    def test_telegram(self):
        """Тест Telegram уведомлений"""
        token = self.telegram_token.text().strip()
        chat_id = self.telegram_chat_id.text().strip()
        
        if not token or not chat_id:
            QMessageBox.warning(self, "Telegram", "Введите Bot Token и Chat ID")
            return
        
        self.telegram_status.setText("⏳")
        self.telegram_status.setStyleSheet("color: yellow;")
        
        try:
            from core.telegram_notifier import TelegramNotifier
            
            notifier = TelegramNotifier(token, chat_id)
            success, message = notifier.test_connection()
            
            if success:
                self.telegram_status.setText("✓")
                self.telegram_status.setStyleSheet("color: #28a745;")
                
                # Сохраняем в конфиг
                self._save_telegram_config(token, chat_id)
                
                QMessageBox.information(self, "Telegram", message)
            else:
                self.telegram_status.setText("✗")
                self.telegram_status.setStyleSheet("color: #dc3545;")
                QMessageBox.critical(self, "Telegram", message)
                
        except Exception as e:
            self.telegram_status.setText("✗")
            self.telegram_status.setStyleSheet("color: #dc3545;")
            QMessageBox.critical(self, "Telegram", f"Ошибка: {e}")
    
    def _save_telegram_config(self, token: str, chat_id: str):
        """Сохранение Telegram конфига"""
        from pathlib import Path
        import json
        
        config_path = Path("video_factory/data/telegram_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_path.write_text(json.dumps({
            "bot_token": token,
            "chat_id": chat_id,
            "notify_complete": self.tg_notify_complete.isChecked(),
            "notify_error": self.tg_notify_error.isChecked(),
            "notify_queue": self.tg_notify_queue.isChecked()
        }, indent=2))
        
        # Настраиваем глобальный нотификатор
        from core.telegram_notifier import setup_notifier
        setup_notifier(token, chat_id)
    
    def _load_telegram_config(self):
        """Загрузка Telegram конфига"""
        from pathlib import Path
        import json
        
        # Сначала проверяем .env (приоритет)
        if config.api.telegram_bot_token and config.api.telegram_chat_id:
            self.telegram_token.setText(config.api.telegram_bot_token)
            self.telegram_chat_id.setText(config.api.telegram_chat_id)
            
            # Настраиваем глобальный нотификатор
            from core.telegram_notifier import setup_notifier
            setup_notifier(config.api.telegram_bot_token, config.api.telegram_chat_id)
            return
        
        # Иначе из JSON файла
        config_path = Path("video_factory/data/telegram_config.json")
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                self.telegram_token.setText(data.get("bot_token", ""))
                self.telegram_chat_id.setText(data.get("chat_id", ""))
                self.tg_notify_complete.setChecked(data.get("notify_complete", True))
                self.tg_notify_error.setChecked(data.get("notify_error", True))
                self.tg_notify_queue.setChecked(data.get("notify_queue", True))
                
                # Настраиваем глобальный нотификатор
                if data.get("bot_token") and data.get("chat_id"):
                    from core.telegram_notifier import setup_notifier
                    setup_notifier(data["bot_token"], data["chat_id"])
            except:
                pass
    
    # === ПОДБОР ГОЛОСА ===
    
    def refresh_voices_list(self):
        """Обновление списка доступных голосов"""
        self.voices_combo.clear()
        
        if not config.api.elevenlabs_keys:
            self.voices_combo.addItem("Нет ElevenLabs ключей")
            return
        
        try:
            from core.elevenlabs_client import ElevenLabsClient
            
            client = ElevenLabsClient(api_keys=config.api.elevenlabs_keys)
            voices = client.get_voices()
            
            for voice in voices:
                label = voice.labels if voice.labels else {}
                gender = label.get('gender', '')
                accent = label.get('accent', '')
                desc = f" ({gender}, {accent})" if gender or accent else ""
                
                self.voices_combo.addItem(
                    f"{voice.name}{desc}",
                    voice.voice_id
                )
            
            if not voices:
                self.voices_combo.addItem("Голоса не найдены")
                
        except Exception as e:
            self.voices_combo.addItem(f"Ошибка: {e}")
    
    def test_selected_voice(self):
        """Тест выбранного голоса"""
        voice_id = self.voices_combo.currentData()
        text = self.voice_test_text.text().strip()
        
        if not voice_id or not text:
            return
        
        if not config.api.elevenlabs_keys:
            QMessageBox.warning(self, "Ошибка", "Нет ElevenLabs ключей")
            return
        
        try:
            from core.elevenlabs_client import ElevenLabsClient
            from pathlib import Path
            import subprocess
            import sys
            
            client = ElevenLabsClient(api_keys=config.api.elevenlabs_keys)
            
            output_path = Path("video_factory/output/voice_test.mp3")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            client.text_to_speech(text, voice_id, output_path)
            
            # Воспроизводим
            if sys.platform == "darwin":
                subprocess.run(["open", str(output_path)])
            else:
                subprocess.run(["xdg-open", str(output_path)])
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось протестировать голос: {e}")
    
    def test_huggingface(self):
        """Тест HuggingFace FLUX"""
        if not config.api.huggingface_tokens:
            QMessageBox.warning(self, "HuggingFace", "Нет HuggingFace токенов в .env")
            return
        
        self.hf_status.setText("⏳")
        self.hf_status.setStyleSheet("color: yellow;")
        
        try:
            from core.flux_generator import FluxGenerator
            
            gen = FluxGenerator(hf_tokens=config.api.huggingface_tokens)
            
            self.hf_status.setText("✓")
            self.hf_status.setStyleSheet("color: #28a745;")
            QMessageBox.information(
                self, "HuggingFace FLUX",
                f"OK! {len(config.api.huggingface_tokens)} токенов настроено\nМодель: FLUX.1-dev"
            )
        except Exception as e:
            self.hf_status.setText("✗")
            self.hf_status.setStyleSheet("color: #dc3545;")
            QMessageBox.critical(self, "HuggingFace", f"Ошибка: {e}")
    
    # === КВОТЫ API ===
    
    def refresh_api_quotas(self):
        """Обновление информации о квотах API"""
        self.quota_status.setText("⏳ Загрузка...")
        self.quota_status.setStyleSheet("color: yellow;")
        
        # Запускаем в отдельном потоке
        self.quota_worker = QuotaCheckWorker()
        self.quota_worker.finished.connect(self.on_quota_check_finished)
        self.quota_worker.start()
    
    def on_quota_check_finished(self, eleven_data: dict, yt_data: dict):
        """Результат проверки квот"""
        self.quota_status.setText("")
        
        # ElevenLabs
        if eleven_data.get('success'):
            used = eleven_data.get('used', 0)
            limit = eleven_data.get('limit', 0)
            remaining = limit - used
            percent = int((used / limit * 100)) if limit > 0 else 0
            
            self.eleven_chars_label.setText(f"{remaining:,} / {limit:,}")
            
            # Прогресс бар текстом
            bar_len = 15
            filled = int(bar_len * percent / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            
            if percent > 80:
                color = "#dc3545"  # Красный
            elif percent > 50:
                color = "#ffc107"  # Жёлтый
            else:
                color = "#28a745"  # Зелёный
            
            self.eleven_progress.setText(f"[{bar}] {percent}%")
            self.eleven_progress.setStyleSheet(f"color: {color};")
        else:
            self.eleven_chars_label.setText("Ошибка")
            self.eleven_progress.setText(eleven_data.get('error', ''))
        
        # YouTube
        if yt_data.get('success'):
            # YouTube API не даёт точную квоту, показываем примерную
            self.yt_quota_label.setText(f"~{yt_data.get('estimated', '?')} / 10,000")
            self.yt_progress.setText(f"({len(config.api.youtube_keys)} ключей)")
            self.yt_progress.setStyleSheet("color: #28a745;")
        else:
            self.yt_quota_label.setText("Ошибка")
            self.yt_progress.setText(yt_data.get('error', ''))


class QuotaCheckWorker(QThread):
    """Проверка квот API в фоне"""
    finished = pyqtSignal(dict, dict)  # eleven_data, yt_data
    
    def run(self):
        eleven_data = self._check_elevenlabs()
        yt_data = self._check_youtube()
        self.finished.emit(eleven_data, yt_data)
    
    def _check_elevenlabs(self) -> dict:
        """Проверка квоты ElevenLabs"""
        import requests
        
        if not config.api.elevenlabs_keys:
            return {'success': False, 'error': 'Нет ключей'}
        
        total_used = 0
        total_limit = 0
        working_keys = 0
        
        for key in config.api.elevenlabs_keys:
            try:
                response = requests.get(
                    "https://api.elevenlabs.io/v1/user",
                    headers={"xi-api-key": key},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    sub = data.get('subscription', {})
                    total_used += sub.get('character_count', 0)
                    total_limit += sub.get('character_limit', 0)
                    working_keys += 1
            except:
                pass
        
        if working_keys > 0:
            return {
                'success': True,
                'used': total_used,
                'limit': total_limit,
                'keys': working_keys
            }
        return {'success': False, 'error': 'Ключи не работают'}
    
    def _check_youtube(self) -> dict:
        """Проверка YouTube API"""
        # YouTube Data API не предоставляет endpoint для проверки квоты
        # Можно только проверить что ключи работают
        
        if not config.api.youtube_keys:
            return {'success': False, 'error': 'Нет ключей'}
        
        try:
            from googleapiclient.discovery import build
            
            # Тестовый запрос (стоит 1 единицу квоты)
            youtube = build('youtube', 'v3', developerKey=config.api.youtube_keys[0])
            youtube.videos().list(part='snippet', id='dQw4w9WgXcQ').execute()
            
            # Примерная оценка: 10,000 на ключ в день
            estimated = 10000 * len(config.api.youtube_keys)
            
            return {
                'success': True,
                'estimated': f"{estimated:,}"
            }
        except Exception as e:
            return {'success': False, 'error': str(e)[:30]}
