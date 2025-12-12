"""
Вкладка генерации медиа (изображения + озвучка) с превью в реальном времени
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QProgressBar, QSplitter, QScrollArea,
    QMessageBox, QFileDialog, QSlider, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
import subprocess
import webbrowser
import sys

sys.path.insert(0, str(__file__).rsplit('/', 3)[0])
from config import config, OUTPUT_DIR


# Импортируем библиотеку голосов
from core.voice_library import (
    VOICE_LIBRARY, VOICE_CATEGORIES, 
    get_all_voices_for_ui, get_voice_by_id
)


class ImageGenWorker(QThread):
    """Воркер для генерации изображений с сигналом для каждой картинки"""
    progress = pyqtSignal(int, int, str)  # current, total, status
    image_ready = pyqtSignal(int, str, bool)  # index, path, success
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, prompts: list, output_dir: Path, style: str = None):
        super().__init__()
        self.prompts = prompts
        self.output_dir = output_dir
        self.style = style
        self.should_stop = False
        self.regenerate_indices = []  # Индексы для перегенерации
    
    def stop(self):
        self.should_stop = True
    
    def add_regenerate(self, index: int):
        """Добавить индекс для перегенерации"""
        if index not in self.regenerate_indices:
            self.regenerate_indices.append(index)
    
    def run(self):
        try:
            from core.image_generator import ImageGenerator
            
            # Используем 4 параллельных потока для ускорения в 4 раза!
            generator = ImageGenerator(self.output_dir, max_workers=4)
            
            def on_progress(current, total, status):
                self.progress.emit(current, total, status)
            
            def on_image_ready(index, path, success):
                self.image_ready.emit(index, path, success)
            
            # ПАРАЛЛЕЛЬНАЯ генерация — в 4 раза быстрее!
            results = generator.generate_batch_parallel(
                self.prompts,
                style=self.style,
                on_progress=on_progress,
                on_image_ready=on_image_ready
            )
            
            self.finished.emit(results)
            
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")


class MediaWorker(QThread):
    """Воркер для генерации промптов и озвучки"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, task_type: str, data: dict):
        super().__init__()
        self.task_type = task_type
        self.data = data
    
    def run(self):
        try:
            if self.task_type == "image_prompts":
                self._generate_image_prompts()
            elif self.task_type == "voice":
                self._generate_voice()
            elif self.task_type == "voice_preview":
                self._preview_voice()
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")
    
    def _generate_image_prompts(self):
        from core.groq_client import GroqClient
        if not config.api.groq_key:
            self.error.emit("Groq API ключ не настроен!")
            return
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        self.progress.emit("Генерация промптов...")
        prompts = groq.generate_image_prompts(
            self.data['script'], self.data.get('style', 'Cinematic')
        )
        self.finished.emit({'type': 'image_prompts', 'data': prompts})
    
    def _generate_voice(self):
        from core.elevenlabs_client import ElevenLabsClient
        if not config.api.elevenlabs_keys:
            self.error.emit("ElevenLabs API ключи не настроены!")
            return
        self.progress.emit("Генерация озвучки...")
        client = ElevenLabsClient(api_keys=config.api.elevenlabs_keys)
        audio_dir = Path(self.data.get('output_dir', OUTPUT_DIR)) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = client.text_to_speech(
            self.data['script'],
            self.data['voice_id'],
            audio_dir / "voiceover.mp3"
        )
        self.finished.emit({'type': 'voice', 'data': [str(audio_path)] if audio_path else []})
    
    def _preview_voice(self):
        from core.elevenlabs_client import ElevenLabsClient
        if not config.api.elevenlabs_keys:
            self.error.emit("ElevenLabs API ключи не настроены!")
            return
        self.progress.emit("Генерация превью...")
        client = ElevenLabsClient(api_keys=config.api.elevenlabs_keys)
        output_path = OUTPUT_DIR / "voice_preview.mp3"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        client.text_to_speech(
            self.data['text'], self.data['voice_id'], output_path,
            stability=self.data.get('stability', 0.5),
            similarity_boost=self.data.get('clarity', 0.75)
        )
        self.finished.emit({'type': 'voice_preview', 'data': str(output_path)})


class ImagePreviewWidget(QFrame):
    """Виджет превью одного изображения с кнопкой перегенерации"""
    regenerate_clicked = pyqtSignal(int)  # index
    
    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.image_path = None
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(160, 130)
        self.setStyleSheet("background: #2d2d2d; border-radius: 5px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Номер
        self.num_label = QLabel(f"#{index + 1}")
        self.num_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.num_label)
        
        # Изображение
        self.image_label = QLabel("⏳")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(150, 85)
        self.image_label.setStyleSheet("background: #1a1a1a; border-radius: 3px;")
        layout.addWidget(self.image_label)
        
        # Кнопка перегенерации
        self.regen_btn = QPushButton("🔄")
        self.regen_btn.setFixedSize(30, 20)
        self.regen_btn.setToolTip("Перегенерировать")
        self.regen_btn.clicked.connect(lambda: self.regenerate_clicked.emit(self.index))
        self.regen_btn.setVisible(False)
        layout.addWidget(self.regen_btn, alignment=Qt.AlignmentFlag.AlignRight)
    
    def set_loading(self):
        self.image_label.setText("⏳")
        self.image_label.setPixmap(QPixmap())
        self.regen_btn.setVisible(False)
    
    def set_image(self, path: str):
        self.image_path = path
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(150, 85, Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.regen_btn.setVisible(True)
        else:
            self.set_error()
    
    def set_error(self):
        self.image_label.setText("❌")
        self.image_label.setPixmap(QPixmap())
        self.regen_btn.setVisible(True)
        self.setStyleSheet("background: #3d2020; border-radius: 5px;")


class MediaTab(QWidget):
    """Вкладка генерации медиа с превью в реальном времени"""
    media_ready = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_script = ""
        self.current_title = ""
        self.image_prompts = []
        self.audio_files = []
        self.loaded_images = []
        self.image_previews = []  # Виджеты превью
        self.worker = None
        self.image_worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # === ВЕРХНЯЯ ПАНЕЛЬ ===
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("🌍 Язык:"))
        self.content_language = QComboBox()
        self.content_language.addItems(["Русский", "English"])
        top_row.addWidget(self.content_language)
        
        top_row.addWidget(QLabel("🎨 Стиль:"))
        self.image_style = QComboBox()
        self.image_style.addItems([
            "cinematic, dramatic lighting, 8k, hyperrealistic",
            "documentary style, historical accuracy, detailed",
            "war photography, dramatic, gritty, realistic",
            "oil painting, classical art, masterpiece",
            "dark fantasy, epic, dramatic lighting",
            "vintage photograph, sepia, historical"
        ])
        top_row.addWidget(self.image_style)
        top_row.addStretch()
        layout.addLayout(top_row)
        
        # === СПЛИТТЕР ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- ЛЕВАЯ: ИЗОБРАЖЕНИЯ ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        # Кнопки генерации
        btn_row = QHBoxLayout()
        self.btn_prompts = QPushButton("📋 1. Промпты")
        self.btn_prompts.clicked.connect(self.generate_image_prompts)
        btn_row.addWidget(self.btn_prompts)
        
        self.btn_generate = QPushButton("🚀 2. Генерировать")
        self.btn_generate.clicked.connect(self.start_image_generation)
        self.btn_generate.setStyleSheet("background: #14a3a8;")
        btn_row.addWidget(self.btn_generate)
        
        self.btn_stop = QPushButton("⏹ Стоп")
        self.btn_stop.clicked.connect(self.stop_image_generation)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background: #e63946;")
        btn_row.addWidget(self.btn_stop)
        left_layout.addLayout(btn_row)
        
        # Прогресс
        self.image_progress = QProgressBar()
        self.image_progress.setVisible(False)
        left_layout.addWidget(self.image_progress)
        
        self.image_status = QLabel("Статус: Ожидание сценария")
        left_layout.addWidget(self.image_status)
        
        # === ПРЕВЬЮ ИЗОБРАЖЕНИЙ ===
        preview_group = QGroupBox("🖼 Превью изображений (в реальном времени)")
        preview_layout = QVBoxLayout(preview_group)
        
        # Скролл для превью
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        
        self.preview_container = QWidget()
        self.preview_grid = QGridLayout(self.preview_container)
        self.preview_grid.setSpacing(5)
        scroll.setWidget(self.preview_container)
        preview_layout.addWidget(scroll)
        
        left_layout.addWidget(preview_group)
        
        # Загрузка готовых
        load_row = QHBoxLayout()
        btn_load = QPushButton("📂 Загрузить готовые")
        btn_load.clicked.connect(self.load_images)
        load_row.addWidget(btn_load)
        
        self.btn_copy_prompts = QPushButton("📋 Копировать промпты")
        self.btn_copy_prompts.clicked.connect(self.copy_all_prompts)
        load_row.addWidget(self.btn_copy_prompts)
        left_layout.addLayout(load_row)
        
        self.images_count = QLabel("Изображений: 0")
        self.images_count.setStyleSheet("font-weight: bold; color: #14a3a8;")
        left_layout.addWidget(self.images_count)
        
        splitter.addWidget(left)
        
        # --- ПРАВАЯ: ОЗВУЧКА ---
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        voice_group = QGroupBox("🎙 Озвучка (ElevenLabs)")
        voice_inner = QVBoxLayout(voice_group)
        
        # Голос с категориями
        voice_row = QHBoxLayout()
        voice_row.addWidget(QLabel("Голос:"))
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(300)
        self._populate_voice_combo()
        voice_row.addWidget(self.voice_combo)
        voice_inner.addLayout(voice_row)
        
        # Описание голоса
        self.voice_description = QLabel("")
        self.voice_description.setStyleSheet("color: #888; font-size: 10px;")
        self.voice_description.setWordWrap(True)
        voice_inner.addWidget(self.voice_description)
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        
        # Стабильность
        stab_row = QHBoxLayout()
        stab_row.addWidget(QLabel("Стабильность:"))
        self.stability = QSlider(Qt.Orientation.Horizontal)
        self.stability.setRange(0, 100)
        self.stability.setValue(50)
        stab_row.addWidget(self.stability)
        self.stability_label = QLabel("50%")
        stab_row.addWidget(self.stability_label)
        self.stability.valueChanged.connect(lambda v: self.stability_label.setText(f"{v}%"))
        voice_inner.addLayout(stab_row)
        
        # Тест
        test_row = QHBoxLayout()
        self.preview_text = QLineEdit("Это тест голоса для озвучки видео.")
        test_row.addWidget(self.preview_text)
        btn_test = QPushButton("▶️")
        btn_test.clicked.connect(self.preview_voice)
        test_row.addWidget(btn_test)
        btn_play = QPushButton("🔊")
        btn_play.clicked.connect(self.play_preview)
        test_row.addWidget(btn_play)
        voice_inner.addLayout(test_row)
        
        # Генерация
        btn_voice = QPushButton("🎙 3. Сгенерировать озвучку")
        btn_voice.clicked.connect(self.generate_voice)
        btn_voice.setStyleSheet("background: #e63946; padding: 8px;")
        voice_inner.addWidget(btn_voice)
        
        self.voice_status = QLabel("Ожидание сценария")
        voice_inner.addWidget(self.voice_status)
        
        right_layout.addWidget(voice_group)
        
        # Субтитры
        srt_row = QHBoxLayout()
        btn_srt = QPushButton("📝 Субтитры")
        btn_srt.clicked.connect(self.generate_srt)
        srt_row.addWidget(btn_srt)
        self.srt_status = QLabel("")
        srt_row.addWidget(self.srt_status)
        right_layout.addLayout(srt_row)
        
        # === УМНЫЙ ПОДБОР МУЗЫКИ ===
        music_group = QGroupBox("🎵 Умный подбор музыки")
        music_layout = QVBoxLayout(music_group)
        
        btn_analyze_music = QPushButton("🎼 Подобрать музыку по сценарию")
        btn_analyze_music.clicked.connect(self.analyze_music)
        btn_analyze_music.setToolTip("AI проанализирует настроение сценария и подберёт музыку")
        music_layout.addWidget(btn_analyze_music)
        
        self.music_result = QTextEdit()
        self.music_result.setMaximumHeight(100)
        self.music_result.setReadOnly(True)
        self.music_result.setPlaceholderText("Результат анализа появится здесь...")
        music_layout.addWidget(self.music_result)
        
        music_btn_row = QHBoxLayout()
        btn_open_library = QPushButton("📚 YouTube Audio Library")
        btn_open_library.clicked.connect(lambda: webbrowser.open("https://studio.youtube.com/channel/UC/music"))
        music_btn_row.addWidget(btn_open_library)
        
        btn_select_music = QPushButton("📂 Выбрать файл")
        btn_select_music.clicked.connect(self.select_music_file)
        music_btn_row.addWidget(btn_select_music)
        music_layout.addLayout(music_btn_row)
        
        self.selected_music_label = QLabel("Музыка: не выбрана")
        self.selected_music_label.setStyleSheet("color: #888;")
        music_layout.addWidget(self.selected_music_label)
        
        right_layout.addWidget(music_group)
        
        # Далее
        btn_next = QPushButton("➡️ К монтажу")
        btn_next.clicked.connect(self.go_to_editor)
        btn_next.setStyleSheet("background: #4CAF50; padding: 10px;")
        right_layout.addWidget(btn_next)
        right_layout.addStretch()
        
        splitter.addWidget(right)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

    
    # === МЕТОДЫ ===
    
    def set_script_data(self, data: dict):
        self.current_title = data.get('title', '')
        self.current_script = data.get('script', '')
        words = len(self.current_script.split()) if self.current_script else 0
        self.voice_status.setText(f"Сценарий: {words} слов")
        self.image_status.setText(f"Сценарий загружен ({words} слов)")
    
    def _populate_voice_combo(self):
        """Заполнение комбобокса голосами по категориям"""
        self.voice_combo.clear()
        
        for category_id, category_info in VOICE_CATEGORIES.items():
            # Добавляем заголовок категории (не выбираемый)
            self.voice_combo.addItem(f"━━━ {category_info['name']} ━━━", None)
            
            # Добавляем голоса этой категории
            added_voices = set()
            for voice in VOICE_LIBRARY.values():
                if voice.name in category_info["voices"] and voice.name not in added_voices:
                    display = f"  {voice.name} ({voice.gender}, {voice.accent})"
                    self.voice_combo.addItem(display, voice.voice_id)
                    added_voices.add(voice.name)
        
        # Выбираем Brian по умолчанию (для военной тематики)
        for i in range(self.voice_combo.count()):
            if self.voice_combo.itemData(i) == "nPczCjzI2devNBz1zQrb":
                self.voice_combo.setCurrentIndex(i)
                break
    
    def _on_voice_changed(self, index: int):
        """Обновление описания при смене голоса"""
        voice_id = self.voice_combo.currentData()
        if voice_id:
            voice = get_voice_by_id(voice_id)
            if voice:
                self.voice_description.setText(f"💡 {voice.description}")
            else:
                self.voice_description.setText("")
        else:
            self.voice_description.setText("")
    
    def get_voice_id(self) -> str:
        voice_id = self.voice_combo.currentData()
        # Если выбран заголовок категории — возвращаем дефолт
        return voice_id if voice_id else "nPczCjzI2devNBz1zQrb"
    
    def _clear_previews(self):
        """Очистка превью"""
        for preview in self.image_previews:
            preview.deleteLater()
        self.image_previews.clear()
    
    def _create_preview_grid(self, count: int):
        """Создание сетки превью"""
        self._clear_previews()
        cols = 5  # 5 картинок в ряд
        
        for i in range(count):
            preview = ImagePreviewWidget(i)
            preview.regenerate_clicked.connect(self._on_regenerate_request)
            self.image_previews.append(preview)
            row = i // cols
            col = i % cols
            self.preview_grid.addWidget(preview, row, col)
    
    def _on_regenerate_request(self, index: int):
        """Запрос на перегенерацию одной картинки"""
        if not self.image_prompts or index >= len(self.image_prompts):
            return
        
        reply = QMessageBox.question(
            self, "Перегенерация",
            f"Перегенерировать изображение #{index + 1}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._regenerate_single(index)
    
    def _regenerate_single(self, index: int):
        """Перегенерация одной картинки"""
        from core.image_generator import ImageGenerator
        
        prompt_data = self.image_prompts[index]
        prompt = prompt_data.get('prompt_en', str(prompt_data)) if isinstance(prompt_data, dict) else str(prompt_data)
        
        output_dir = OUTPUT_DIR / "images" / (self.current_title or "video")
        generator = ImageGenerator(output_dir)
        
        self.image_previews[index].set_loading()
        self.image_status.setText(f"Перегенерация #{index + 1}...")
        
        # Запускаем в отдельном потоке
        import threading
        def regen():
            result = generator.generate_single(prompt, f"{index+1:03d}_scene", self.image_style.currentText(), max_retries=3)
            # Обновляем UI в главном потоке
            from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
            if result.success and result.path:
                self.image_previews[index].set_image(str(result.path))
                self.loaded_images[index] = result.path
            else:
                self.image_previews[index].set_error()
            self.image_status.setText("Готово")
        
        threading.Thread(target=regen, daemon=True).start()
    
    # --- Промпты ---
    
    def generate_image_prompts(self):
        if not self.current_script:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите сценарий")
            return
        self.image_status.setText("Генерация промптов...")
        self.btn_prompts.setEnabled(False)
        
        self.worker = MediaWorker("image_prompts", {
            'script': self.current_script,
            'style': self.image_style.currentText()
        })
        self.worker.progress.connect(lambda m: self.image_status.setText(m))
        self.worker.finished.connect(self._on_prompts_ready)
        self.worker.error.connect(self._on_error)
        self.worker.start()
    
    def _on_prompts_ready(self, result: dict):
        self.btn_prompts.setEnabled(True)
        if result.get('type') == 'image_prompts':
            self.image_prompts = result['data']
            self.image_status.setText(f"✅ {len(self.image_prompts)} промптов готово")
            
            # Создаём сетку превью
            self._create_preview_grid(len(self.image_prompts))
            
            QMessageBox.information(
                self, "Готово", 
                f"Сгенерировано {len(self.image_prompts)} промптов!\n\n"
                "Нажмите '🚀 Генерировать' для создания изображений."
            )
    
    def copy_all_prompts(self):
        from PyQt6.QtWidgets import QApplication
        if not self.image_prompts:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте промпты")
            return
        
        text = ""
        for i, p in enumerate(self.image_prompts, 1):
            prompt = p.get('prompt_en', str(p)) if isinstance(p, dict) else str(p)
            text += f"[{i}] {prompt}\n\n"
        
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Скопировано", f"{len(self.image_prompts)} промптов в буфере")
    
    # --- Генерация изображений ---
    
    def start_image_generation(self):
        if not self.image_prompts:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте промпты")
            return
        
        # Создаём папку
        output_dir = OUTPUT_DIR / "images" / (self.current_title or "video")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.btn_generate.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.image_progress.setVisible(True)
        self.image_progress.setRange(0, len(self.image_prompts))
        self.image_progress.setValue(0)
        
        # Сбрасываем превью
        for preview in self.image_previews:
            preview.set_loading()
        
        self.image_worker = ImageGenWorker(
            self.image_prompts, 
            output_dir,
            self.image_style.currentText()
        )
        self.image_worker.progress.connect(self._on_image_progress)
        self.image_worker.image_ready.connect(self._on_single_image_ready)
        self.image_worker.finished.connect(self._on_images_finished)
        self.image_worker.error.connect(self._on_error)
        self.image_worker.start()
    
    def stop_image_generation(self):
        if self.image_worker:
            self.image_worker.stop()
            self.image_status.setText("Остановлено")
            self.btn_generate.setEnabled(True)
            self.btn_stop.setEnabled(False)
    
    def _on_image_progress(self, current: int, total: int, status: str):
        self.image_progress.setValue(current)
        self.image_status.setText(status)
    
    def _on_single_image_ready(self, index: int, path: str, success: bool):
        """Обновление превью одной картинки"""
        if index < len(self.image_previews):
            if success and path:
                self.image_previews[index].set_image(path)
            else:
                self.image_previews[index].set_error()
    
    def _on_images_finished(self, results: list):
        self.btn_generate.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.image_progress.setVisible(False)
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        self.loaded_images = [r.path for r in results if r.success and r.path]
        self.images_count.setText(f"Изображений: {len(self.loaded_images)}")
        self.image_status.setText(f"✅ Готово: {len(successful)}/{len(results)}")
        
        if failed:
            QMessageBox.warning(
                self, "Частичный успех",
                f"Успешно: {len(successful)}\nОшибок: {len(failed)}\n\n"
                "Нажмите 🔄 на красных картинках для перегенерации."
            )
        else:
            QMessageBox.information(self, "Готово", f"Все {len(successful)} изображений готовы!")
    
    # --- Загрузка ---
    
    def load_images(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            folder = Path(folder)
            images = sorted(
                list(folder.glob("*.png")) + list(folder.glob("*.jpg")) + 
                list(folder.glob("*.jpeg")) + list(folder.glob("*.webp"))
            )
            self.loaded_images = images
            self.images_count.setText(f"Изображений: {len(self.loaded_images)}")
            
            # Показываем превью
            self._create_preview_grid(len(images))
            for i, img_path in enumerate(images):
                self.image_previews[i].set_image(str(img_path))
    
    # --- Озвучка ---
    
    def preview_voice(self):
        text = self.preview_text.text().strip()
        if not text:
            return
        self.voice_status.setText("Генерация превью...")
        self.worker = MediaWorker("voice_preview", {
            'text': text,
            'voice_id': self.get_voice_id(),
            'stability': self.stability.value() / 100,
            'clarity': 0.75
        })
        self.worker.progress.connect(lambda m: self.voice_status.setText(m))
        self.worker.finished.connect(self._on_voice_result)
        self.worker.error.connect(self._on_error)
        self.worker.start()
    
    def play_preview(self):
        preview_path = OUTPUT_DIR / "voice_preview.mp3"
        if preview_path.exists():
            if sys.platform == "darwin":
                subprocess.run(["open", str(preview_path)])
            else:
                subprocess.run(["xdg-open", str(preview_path)])
    
    def generate_voice(self):
        if not self.current_script:
            QMessageBox.warning(self, "Ошибка", "Нет сценария")
            return
        
        words = len(self.current_script.split())
        reply = QMessageBox.question(
            self, "Генерация озвучки",
            f"Сгенерировать озвучку?\n\nСлов: {words}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.voice_status.setText("Генерация...")
            self.worker = MediaWorker("voice", {
                'script': self.current_script,
                'voice_id': self.get_voice_id(),
                'output_dir': str(OUTPUT_DIR)
            })
            self.worker.progress.connect(lambda m: self.voice_status.setText(m))
            self.worker.finished.connect(self._on_voice_result)
            self.worker.error.connect(self._on_error)
            self.worker.start()
    
    def _on_voice_result(self, result: dict):
        t = result.get('type')
        if t == 'voice':
            self.audio_files = result['data']
            self.voice_status.setText("✅ Озвучка готова")
            QMessageBox.information(self, "Готово", "Озвучка сгенерирована!")
        elif t == 'voice_preview':
            self.voice_status.setText("✅ Превью готово")
    
    def generate_srt(self):
        if not self.current_script:
            return
        from core.srt_generator import SRTGenerator
        srt = SRTGenerator()
        path = OUTPUT_DIR / f"{self.current_title or 'video'}.srt"
        path.parent.mkdir(parents=True, exist_ok=True)
        srt.generate_from_script(self.current_script, path)
        self.srt_status.setText(f"✅ {path.name}")
    
    def _on_error(self, msg: str):
        self.btn_generate.setEnabled(True)
        self.btn_prompts.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.image_progress.setVisible(False)
        QMessageBox.critical(self, "Ошибка", msg)
    
    def analyze_music(self):
        """Умный подбор музыки по сценарию"""
        if not self.current_script:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите сценарий")
            return
        
        self.music_result.setText("⏳ Анализ настроения сценария...")
        
        try:
            from core.youtube_music import SmartMusicSelector
            
            selector = SmartMusicSelector()
            result = selector.get_music_recommendation(self.current_script)
            
            analysis = result.get('analysis', {})
            tips = result.get('tips', [])
            suggestions = result.get('search_suggestions', [])
            local_matches = result.get('local_matches', [])
            
            text = f"""🎭 Основное настроение: {analysis.get('primary_mood', '?')}
🎵 Дополнительные: {', '.join(analysis.get('secondary_moods', []))}
⚡ Интенсивность: {analysis.get('intensity', '?')}
🎼 Темп: {analysis.get('tempo', '?')}

📋 Поисковые запросы для YouTube Audio Library:
{chr(10).join('• ' + s for s in suggestions)}

💡 Советы:
{chr(10).join('• ' + t for t in tips)}"""
            
            if local_matches:
                text += f"\n\n📂 Найдено локально: {len(local_matches)} треков"
            
            self.music_result.setText(text)
            
        except Exception as e:
            self.music_result.setText(f"❌ Ошибка: {e}")
    
    def select_music_file(self):
        """Выбор файла музыки"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите музыку",
            "",
            "Audio Files (*.mp3 *.wav *.m4a)"
        )
        
        if file_path:
            self.selected_music = file_path
            self.selected_music_label.setText(f"🎵 {Path(file_path).name}")
            self.selected_music_label.setStyleSheet("color: #28a745;")
    
    def go_to_editor(self):
        if not self.loaded_images:
            QMessageBox.warning(self, "Ошибка", "Нет изображений")
            return
        
        music_path = getattr(self, 'selected_music', None)
        
        self.media_ready.emit({
            'images': [str(p) for p in self.loaded_images],
            'audio': self.audio_files[0] if self.audio_files else None,
            'music': music_path,
            'title': self.current_title
        })
        QMessageBox.information(self, "Готово", "Перейдите на вкладку 'Монтаж'")
