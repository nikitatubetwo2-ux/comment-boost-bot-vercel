"""
Вкладка монтажа видео
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QListWidget, QProgressBar, QSplitter,
    QSlider, QCheckBox, QSpinBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config import config, OUTPUT_DIR


class RenderWorker(QThread):
    """Фоновый поток для рендера"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, data: dict):
        super().__init__()
        self.data = data
    
    def run(self):
        try:
            from core.video_editor import VideoEditor, VideoConfig
            
            self.progress.emit(10, "Подготовка...")
            
            # Конфигурация
            video_config = VideoConfig(
                resolution=tuple(map(int, self.data['resolution'].split('x'))),
                fps=self.data['fps'],
                enable_zoom=self.data['enable_zoom'],
                min_zoom=self.data['min_zoom'] / 100,
                max_zoom=self.data['max_zoom'] / 100,
                transition_type=self.data['transition_type'],
                transition_duration=self.data['transition_duration'] / 1000,
                color_grade=self.data['color_grade']
            )
            
            editor = VideoEditor(video_config)
            
            self.progress.emit(20, "Загрузка изображений...")
            
            images = [Path(p) for p in self.data['images']]
            audio_path = Path(self.data['audio'])
            output_path = Path(self.data['output'])
            
            music_path = None
            if self.data.get('music'):
                music_path = Path(self.data['music'])
            
            self.progress.emit(40, "Создание видео...")
            
            editor.create_video_simple(
                images,
                audio_path,
                output_path,
                music_path,
                self.data.get('music_volume', 0.15)
            )
            
            self.progress.emit(100, "Готово!")
            self.finished.emit(str(output_path))
            
        except Exception as e:
            self.error.emit(str(e))


class EditorTab(QWidget):
    """Вкладка для монтажа видео"""
    
    def __init__(self):
        super().__init__()
        self.images = []
        self.audio_path = None
        self.music_path = None
        self.title = "video"
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Глобальная стилизация для SpinBox
        spinbox_style = """
            QSpinBox {
                background: #2d2d2d;
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                padding: 4px 8px;
                color: #e0e0e0;
                min-width: 80px;
            }
            QSpinBox:hover {
                border-color: #14a3a8;
            }
            QSpinBox:focus {
                border-color: #1abc9c;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #3a3a3a;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #14a3a8;
            }
        """
        self.setStyleSheet(self.styleSheet() + spinbox_style)
        
        # Верхняя панель - информация о проекте
        info_group = QGroupBox("📁 Материалы проекта")
        info_layout = QVBoxLayout(info_group)
        
        # Статус материалов
        materials_layout = QHBoxLayout()
        
        self.images_label = QLabel("🖼 Изображения: не загружены")
        materials_layout.addWidget(self.images_label)
        
        self.audio_label = QLabel("🎙 Озвучка: не загружена")
        materials_layout.addWidget(self.audio_label)
        
        self.music_label = QLabel("🎵 Музыка: не выбрана")
        materials_layout.addWidget(self.music_label)
        
        info_layout.addLayout(materials_layout)
        
        # Кнопки загрузки
        load_layout = QHBoxLayout()
        
        btn_load_images = QPushButton("📂 Загрузить изображения")
        btn_load_images.clicked.connect(self.load_images)
        load_layout.addWidget(btn_load_images)
        
        btn_load_audio = QPushButton("🎙 Загрузить озвучку")
        btn_load_audio.clicked.connect(self.load_audio)
        load_layout.addWidget(btn_load_audio)
        
        btn_load_music = QPushButton("🎵 Выбрать музыку")
        btn_load_music.clicked.connect(self.load_music)
        load_layout.addWidget(btn_load_music)
        
        info_layout.addLayout(load_layout)
        layout.addWidget(info_group)
        
        # Нижняя часть - настройки
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - эффекты
        effects_panel = QWidget()
        effects_layout = QVBoxLayout(effects_panel)
        
        # Эффекты зума
        zoom_group = QGroupBox("🔍 Эффект Ken Burns (плавный зум)")
        zoom_group.setStyleSheet("QGroupBox { background: #2a2a2a; border-radius: 8px; }")
        zoom_layout = QVBoxLayout(zoom_group)
        
        self.enable_zoom = QCheckBox("Включить плавное приближение/отдаление")
        self.enable_zoom.setChecked(True)
        self.enable_zoom.setStyleSheet("padding: 5px;")
        zoom_layout.addWidget(self.enable_zoom)
        
        zoom_layout.addWidget(QLabel("💡 Создаёт эффект движения на статичных изображениях"))
        
        zoom_settings = QHBoxLayout()
        zoom_settings.addWidget(QLabel("Мин. зум:"))
        self.min_zoom = QSpinBox()
        self.min_zoom.setRange(100, 150)
        self.min_zoom.setValue(100)
        self.min_zoom.setSuffix("%")
        self.min_zoom.setStyleSheet("padding: 5px;")
        zoom_settings.addWidget(self.min_zoom)
        
        zoom_settings.addWidget(QLabel("Макс. зум:"))
        self.max_zoom = QSpinBox()
        self.max_zoom.setRange(100, 150)
        self.max_zoom.setValue(120)
        self.max_zoom.setSuffix("%")
        self.max_zoom.setStyleSheet("padding: 5px;")
        zoom_settings.addWidget(self.max_zoom)
        zoom_layout.addLayout(zoom_settings)
        
        effects_layout.addWidget(zoom_group)
        
        # Переходы
        transitions_group = QGroupBox("✨ Переходы между сценами")
        transitions_group.setStyleSheet("QGroupBox { background: #2a2a2a; border-radius: 8px; }")
        transitions_layout = QVBoxLayout(transitions_group)
        
        trans_type = QHBoxLayout()
        trans_type.addWidget(QLabel("Тип перехода:"))
        self.transition_type = QComboBox()
        self.transition_type.addItems([
            "fade - Плавное затухание",
            "dissolve - Растворение",
            "crossfade - Перекрёстное затухание",
            "slide_left - Сдвиг влево",
            "slide_right - Сдвиг вправо",
            "slide_up - Сдвиг вверх",
            "slide_down - Сдвиг вниз",
            "zoom_in - Приближение",
            "zoom_out - Отдаление",
            "wipe - Шторка",
            "blur - Размытие",
            "none - Без перехода"
        ])
        self.transition_type.setStyleSheet("padding: 5px;")
        trans_type.addWidget(self.transition_type)
        transitions_layout.addLayout(trans_type)
        
        # Описание перехода
        self.transition_desc = QLabel("💡 Плавное затухание между кадрами")
        self.transition_desc.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        self.transition_type.currentTextChanged.connect(self._update_transition_desc)
        transitions_layout.addWidget(self.transition_desc)
        
        trans_duration = QHBoxLayout()
        trans_duration.addWidget(QLabel("Длительность:"))
        self.transition_duration = QSpinBox()
        self.transition_duration.setRange(100, 2000)
        self.transition_duration.setValue(500)
        self.transition_duration.setSuffix(" мс")
        self.transition_duration.setStyleSheet("padding: 5px;")
        trans_duration.addWidget(self.transition_duration)
        transitions_layout.addLayout(trans_duration)
        
        effects_layout.addWidget(transitions_group)
        
        # Цветокоррекция
        color_group = QGroupBox("🎨 Цветокоррекция / Фильтры")
        color_group.setStyleSheet("QGroupBox { background: #2a2a2a; border-radius: 8px; }")
        color_layout = QVBoxLayout(color_group)
        
        color_layout.addWidget(QLabel("Применить фильтр к изображениям:"))
        
        self.color_grade = QComboBox()
        self.color_grade.addItems([
            "none - Без фильтра",
            "cinematic - Кинематографичный",
            "warm - Тёплые тона",
            "cold - Холодные тона",
            "vintage - Винтаж/Ретро",
            "dramatic - Драматичный",
            "noir - Чёрно-белый нуар",
            "sepia - Сепия",
            "vibrant - Яркие цвета",
            "muted - Приглушённые тона",
            "high_contrast - Высокий контраст",
            "soft - Мягкий свет",
            "dark - Тёмный/Мрачный",
            "golden_hour - Золотой час"
        ])
        self.color_grade.setStyleSheet("padding: 5px;")
        color_layout.addWidget(self.color_grade)
        
        # Описание фильтра
        self.color_desc = QLabel("💡 Оригинальные цвета без изменений")
        self.color_desc.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        self.color_grade.currentTextChanged.connect(self._update_color_desc)
        color_layout.addWidget(self.color_desc)
        
        effects_layout.addWidget(color_group)
        effects_layout.addStretch()
        
        splitter.addWidget(effects_panel)
        
        # Центральная панель - музыка
        music_panel = QWidget()
        music_layout = QVBoxLayout(music_panel)
        
        music_group = QGroupBox("🎵 Фоновая музыка")
        music_inner = QVBoxLayout(music_group)
        
        music_inner.addWidget(QLabel("Источник: YouTube Audio Library"))
        
        btn_open_yt_audio = QPushButton("🔗 Открыть YouTube Audio Library")
        btn_open_yt_audio.clicked.connect(self.open_youtube_audio)
        music_inner.addWidget(btn_open_yt_audio)
        
        # Громкость
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Громкость:"))
        self.music_volume = QSlider(Qt.Orientation.Horizontal)
        self.music_volume.setRange(0, 100)
        self.music_volume.setValue(15)
        # Стилизация слайдера
        self.music_volume.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #3a3a3a;
                height: 8px;
                background: #2d2d2d;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #14a3a8;
                border: 2px solid #0d7377;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #1abc9c;
            }
            QSlider::sub-page:horizontal {
                background: #14a3a8;
                border-radius: 4px;
            }
        """)
        volume_layout.addWidget(self.music_volume)
        self.volume_label = QLabel("15%")
        self.volume_label.setStyleSheet("color: #14a3a8; font-weight: bold; min-width: 40px;")
        volume_layout.addWidget(self.volume_label)
        self.music_volume.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        music_inner.addLayout(volume_layout)
        
        music_layout.addWidget(music_group)
        
        # Copyright проверка
        copyright_group = QGroupBox("⚠️ Проверка Copyright")
        copyright_layout = QVBoxLayout(copyright_group)
        
        btn_check_copyright = QPushButton("🔍 Проверить материалы")
        btn_check_copyright.clicked.connect(self.check_copyright)
        copyright_layout.addWidget(btn_check_copyright)
        
        self.copyright_status = QTextEdit()
        self.copyright_status.setMaximumHeight(100)
        self.copyright_status.setReadOnly(True)
        copyright_layout.addWidget(self.copyright_status)
        
        music_layout.addWidget(copyright_group)
        music_layout.addStretch()
        
        splitter.addWidget(music_panel)
        
        # Правая панель - рендер
        render_panel = QWidget()
        render_layout = QVBoxLayout(render_panel)
        
        render_group = QGroupBox("🎬 Рендер видео")
        render_inner = QVBoxLayout(render_group)
        
        # Название
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название:"))
        self.output_name = QLineEdit()
        self.output_name.setPlaceholderText("video")
        name_layout.addWidget(self.output_name)
        render_inner.addLayout(name_layout)
        
        # Качество
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Качество:"))
        self.render_quality = QComboBox()
        self.render_quality.addItems([
            "1920x1080",
            "2560x1440",
            "3840x2160"
        ])
        quality_layout.addWidget(self.render_quality)
        render_inner.addLayout(quality_layout)
        
        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.render_fps = QComboBox()
        self.render_fps.addItems(["24", "30", "60"])
        self.render_fps.setCurrentIndex(1)
        fps_layout.addWidget(self.render_fps)
        render_inner.addLayout(fps_layout)
        
        # Кнопка рендера
        btn_render = QPushButton("🎬 Начать рендер")
        btn_render.setStyleSheet("""
            QPushButton {
                background-color: #e63946;
                font-size: 16px;
                padding: 15px;
            }
        """)
        btn_render.clicked.connect(self.start_render)
        render_inner.addWidget(btn_render)
        
        # Прогресс
        self.render_progress = QProgressBar()
        self.render_progress.setVisible(False)
        render_inner.addWidget(self.render_progress)
        
        self.render_status = QLabel("Статус: Готов к рендеру")
        render_inner.addWidget(self.render_status)
        
        render_layout.addWidget(render_group)
        render_layout.addStretch()
        
        splitter.addWidget(render_panel)
        splitter.setSizes([300, 350, 350])
        
        layout.addWidget(splitter)
    
    def set_media_data(self, data: dict):
        """Установка данных из вкладки Медиа"""
        self.images = data.get('images', [])
        self.audio_path = data.get('audio')
        self.title = data.get('title', 'video')
        
        self.images_label.setText(f"🖼 Изображения: {len(self.images)} шт.")
        
        if self.audio_path:
            self.audio_label.setText(f"🎙 Озвучка: загружена ✓")
        
        self.output_name.setText(self.title)
    
    def load_images(self):
        """Загрузка изображений"""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с изображениями")
        
        if folder:
            folder_path = Path(folder)
            images = list(folder_path.glob("*.png")) + list(folder_path.glob("*.jpg"))
            self.images = sorted([str(p) for p in images])
            self.images_label.setText(f"🖼 Изображения: {len(self.images)} шт.")
    
    def load_audio(self):
        """Загрузка озвучки"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите аудио файл",
            "", "Audio Files (*.mp3 *.wav *.m4a)"
        )
        
        if filepath:
            self.audio_path = filepath
            self.audio_label.setText(f"🎙 Озвучка: загружена ✓")
    
    def load_music(self):
        """Загрузка фоновой музыки"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите музыку",
            "", "Audio Files (*.mp3 *.wav *.m4a)"
        )
        
        if filepath:
            self.music_path = filepath
            self.music_label.setText(f"🎵 Музыка: выбрана ✓")
    
    def open_youtube_audio(self):
        """Открыть YouTube Audio Library"""
        import subprocess
        subprocess.Popen(['open', "https://studio.youtube.com/channel/UC/music"])
    
    def check_copyright(self):
        """Проверка на copyright"""
        from core.copyright_checker import CopyrightChecker
        
        checker = CopyrightChecker()
        
        # Проверяем изображения
        images_info = [{'source': 'ai_generated', 'path': p} for p in self.images]
        
        # Проверяем музыку
        music_info = {
            'source': 'youtube audio library' if self.music_path else 'none',
            'title': Path(self.music_path).name if self.music_path else 'Нет'
        }
        
        result = checker.check_project(images_info, music_info, 'ai_generated')
        
        self.copyright_status.setText(f"""
{result['overall_message']}

✅ Безопасно: {result['safe_count']}
⚠️ Предупреждения: {result['warning_count']}
❌ Проблемы: {result['danger_count']}
        """)
    
    def start_render(self):
        """Запуск рендера"""
        if not self.images:
            QMessageBox.warning(self, "Ошибка", "Загрузите изображения")
            return
        
        if not self.audio_path:
            QMessageBox.warning(self, "Ошибка", "Загрузите озвучку")
            return
        
        output_name = self.output_name.text().strip() or "video"
        output_path = OUTPUT_DIR / f"{output_name}.mp4"
        
        self.render_progress.setVisible(True)
        self.render_progress.setValue(0)
        self.render_status.setText("Статус: Рендеринг...")
        
        self.worker = RenderWorker({
            'images': self.images,
            'audio': self.audio_path,
            'music': self.music_path,
            'music_volume': self.music_volume.value() / 100,
            'output': str(output_path),
            'resolution': self.render_quality.currentText(),
            'fps': int(self.render_fps.currentText()),
            'enable_zoom': self.enable_zoom.isChecked(),
            'min_zoom': self.min_zoom.value(),
            'max_zoom': self.max_zoom.value(),
            'transition_type': self.transition_type.currentText(),
            'transition_duration': self.transition_duration.value(),
            'color_grade': self.color_grade.currentText()
        })
        
        self.worker.progress.connect(self.on_render_progress)
        self.worker.finished.connect(self.on_render_finished)
        self.worker.error.connect(self.on_render_error)
        self.worker.start()
    
    def on_render_progress(self, value: int, message: str):
        self.render_progress.setValue(value)
        self.render_status.setText(f"Статус: {message}")
    
    def on_render_finished(self, output_path: str):
        self.render_progress.setVisible(False)
        self.render_status.setText(f"Статус: Готово! {output_path}")
        
        QMessageBox.information(
            self, "Рендер завершён",
            f"Видео сохранено:\n{output_path}"
        )
    
    def on_render_error(self, message: str):
        self.render_progress.setVisible(False)
        self.render_status.setText("Статус: Ошибка")
        QMessageBox.critical(self, "Ошибка рендера", message)
    
    def _update_transition_desc(self, text: str):
        """Обновление описания перехода"""
        descriptions = {
            "fade": "💡 Плавное затухание между кадрами",
            "dissolve": "💡 Один кадр растворяется в другом",
            "crossfade": "💡 Перекрёстное наложение двух кадров",
            "slide_left": "💡 Новый кадр выезжает слева",
            "slide_right": "💡 Новый кадр выезжает справа",
            "slide_up": "💡 Новый кадр выезжает снизу",
            "slide_down": "💡 Новый кадр выезжает сверху",
            "zoom_in": "💡 Приближение к центру при смене",
            "zoom_out": "💡 Отдаление от центра при смене",
            "wipe": "💡 Шторка стирает старый кадр",
            "blur": "💡 Размытие при переходе",
            "none": "💡 Резкая смена без эффекта"
        }
        key = text.split(" - ")[0] if " - " in text else text
        self.transition_desc.setText(descriptions.get(key, ""))
    
    def _update_color_desc(self, text: str):
        """Обновление описания фильтра"""
        descriptions = {
            "none": "💡 Оригинальные цвета без изменений",
            "cinematic": "💡 Голливудский стиль с глубокими тенями",
            "warm": "💡 Тёплые оранжево-жёлтые оттенки",
            "cold": "💡 Холодные синие оттенки",
            "vintage": "💡 Эффект старой плёнки",
            "dramatic": "💡 Высокий контраст, насыщенные цвета",
            "noir": "💡 Чёрно-белый с высоким контрастом",
            "sepia": "💡 Коричневые тона под старину",
            "vibrant": "💡 Яркие насыщенные цвета",
            "muted": "💡 Приглушённая пастельная палитра",
            "high_contrast": "💡 Резкие переходы свет/тень",
            "soft": "💡 Мягкое освещение, нежные тона",
            "dark": "💡 Тёмная атмосфера, глубокие тени",
            "golden_hour": "💡 Тёплый закатный свет"
        }
        key = text.split(" - ")[0] if " - " in text else text
        self.color_desc.setText(descriptions.get(key, ""))
