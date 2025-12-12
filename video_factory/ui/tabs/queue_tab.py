"""
Вкладка очереди проектов — пакетная генерация видео
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QProgressBar, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QScrollArea, QGridLayout,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QSpinBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPixmap
from pathlib import Path
import sys

sys.path.insert(0, str(__file__).rsplit('/', 3)[0])
from config import OUTPUT_DIR


class QueueWorker(QThread):
    """Воркер для обработки очереди"""
    progress = pyqtSignal(str, int)  # project_id, progress
    status_changed = pyqtSignal(str, str)  # project_id, status
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline
    
    def run(self):
        try:
            self.pipeline.start_queue()
            while self.pipeline.is_running:
                import time
                time.sleep(1)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class NewProjectDialog(QDialog):
    """Диалог создания нового проекта с выбором профиля канала"""
    
    def __init__(self, channel_styles: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Новый проект")
        self.setMinimumWidth(550)
        self.channel_styles = channel_styles or []
        
        layout = QVBoxLayout(self)
        
        # Инструкция
        info = QLabel("🎬 Создайте проект → добавьте в очередь → запустите → уйдите спать → утром проверьте!")
        info.setStyleSheet("color: #14a3a8; font-size: 12px; padding: 10px; background: #1a3a3a; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        form = QFormLayout()
        
        # === ПРОФИЛЬ КАНАЛА ===
        profile_row = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("➕ Новый канал (без профиля)", "")
        for style in self.channel_styles:
            self.profile_combo.addItem(f"📺 {style.name} ({style.sub_niche or style.main_niche})", style.id)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        profile_row.addWidget(self.profile_combo)
        
        btn_manage = QPushButton("⚙️")
        btn_manage.setToolTip("Управление профилями")
        btn_manage.setFixedWidth(40)
        profile_row.addWidget(btn_manage)
        form.addRow("Профиль канала:", profile_row)
        
        # Инфо о профиле
        self.profile_info = QLabel("")
        self.profile_info.setStyleSheet("color: #14a3a8; font-size: 11px;")
        self.profile_info.setWordWrap(True)
        form.addRow("", self.profile_info)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название проекта/видео")
        form.addRow("Название:", self.name_edit)
        
        self.topic_edit = QTextEdit()
        self.topic_edit.setMaximumHeight(80)
        self.topic_edit.setPlaceholderText("Тема видео (подробно)")
        form.addRow("Тема:", self.topic_edit)
        
        self.competitor_edit = QLineEdit()
        self.competitor_edit.setPlaceholderText("@channel или URL (для нового профиля)")
        form.addRow("Конкурент:", self.competitor_edit)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "10-20 минут",
            "20-30 минут", 
            "30-40 минут",
            "40-50 минут",
            "50-60 минут",
            "60+ минут"
        ])
        self.duration_combo.setCurrentIndex(1)
        form.addRow("Длительность:", self.duration_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Русский", "English"])
        form.addRow("Язык:", self.language_combo)
        
        layout.addLayout(form)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _on_profile_changed(self, index: int):
        """При выборе профиля показываем его настройки"""
        style_id = self.profile_combo.currentData()
        if style_id:
            for style in self.channel_styles:
                if style.id == style_id:
                    self.profile_info.setText(
                        f"🎙 Голос: {style.voice_name}\n"
                        f"🎨 Стиль: {style.image_style[:40]}...\n"
                        f"🎵 Музыка: {style.music_mood}"
                    )
                    self.competitor_edit.setEnabled(False)
                    self.competitor_edit.setText(style.competitor_channel)
                    break
        else:
            self.profile_info.setText("Будет создан новый профиль на основе анализа конкурента")
            self.competitor_edit.setEnabled(True)
            self.competitor_edit.setText("")
    
    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "topic": self.topic_edit.toPlainText().strip(),
            "competitor": self.competitor_edit.text().strip(),
            "channel_style_id": self.profile_combo.currentData() or "",
            "duration": self.duration_combo.currentText(),
            "language": self.language_combo.currentText()
        }


class BatchProjectsDialog(QDialog):
    """Диалог для быстрого добавления НЕСКОЛЬКИХ проектов сразу"""
    
    def __init__(self, channel_styles: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Пакетное добавление проектов")
        self.setMinimumSize(600, 500)
        self.channel_styles = channel_styles or []
        
        layout = QVBoxLayout(self)
        
        # Инструкция
        info = QLabel(
            "🚀 Добавьте несколько тем сразу!\n"
            "Каждая тема на новой строке. Формат: Название | Тема (подробно)\n"
            "Пример: Битва за Сталинград | Подробная история битвы за Сталинград 1942-1943"
        )
        info.setStyleSheet("color: #14a3a8; padding: 10px; background: #1a3a3a; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Профиль канала
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Профиль канала:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("➕ Без профиля", "")
        for style in self.channel_styles:
            self.profile_combo.addItem(f"📺 {style.name}", style.id)
        profile_row.addWidget(self.profile_combo)
        layout.addLayout(profile_row)
        
        # Длительность
        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Длительность всех:"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "10-20 минут", "20-30 минут", "30-40 минут",
            "40-50 минут", "50-60 минут", "60+ минут"
        ])
        self.duration_combo.setCurrentIndex(2)  # 30-40 по умолчанию
        dur_row.addWidget(self.duration_combo)
        dur_row.addStretch()
        layout.addLayout(dur_row)
        
        # Текстовое поле для тем
        layout.addWidget(QLabel("📝 Темы (каждая на новой строке):"))
        self.topics_edit = QTextEdit()
        self.topics_edit.setPlaceholderText(
            "Битва за Сталинград | Подробная история битвы за Сталинград\n"
            "Курская дуга | Крупнейшее танковое сражение в истории\n"
            "Операция Барбаросса | Начало войны на Восточном фронте"
        )
        layout.addWidget(self.topics_edit)
        
        # Счётчик
        self.count_label = QLabel("Проектов: 0")
        self.count_label.setStyleSheet("font-weight: bold;")
        self.topics_edit.textChanged.connect(self._update_count)
        layout.addWidget(self.count_label)
        
        # Кнопки
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        
        btn_add = QPushButton("➕ Добавить все в очередь")
        btn_add.setStyleSheet("background: #4CAF50; padding: 10px;")
        btn_add.clicked.connect(self.accept)
        btn_row.addWidget(btn_add)
        layout.addLayout(btn_row)
    
    def _update_count(self):
        lines = [l.strip() for l in self.topics_edit.toPlainText().split('\n') if l.strip()]
        self.count_label.setText(f"Проектов: {len(lines)}")
    
    def get_projects(self) -> list:
        """Возвращает список проектов для добавления"""
        projects = []
        lines = [l.strip() for l in self.topics_edit.toPlainText().split('\n') if l.strip()]
        
        for line in lines:
            if '|' in line:
                parts = line.split('|', 1)
                name = parts[0].strip()
                topic = parts[1].strip()
            else:
                name = line[:50]
                topic = line
            
            projects.append({
                "name": name,
                "topic": topic,
                "channel_style_id": self.profile_combo.currentData() or "",
                "duration": self.duration_combo.currentText(),
                "language": "Русский"
            })
        
        return projects


class ProjectPreviewDialog(QDialog):
    """Диалог просмотра и редактирования проекта"""
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(f"Проект: {project.name}")
        self.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Статус
        status_row = QHBoxLayout()
        status_label = QLabel(f"Статус: {project.status}")
        status_label.setStyleSheet(self._get_status_style(project.status))
        status_row.addWidget(status_label)
        status_row.addStretch()
        layout.addLayout(status_row)
        
        # Сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая часть — изображения
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("🖼 Изображения:"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        images_widget = QWidget()
        self.images_grid = QGridLayout(images_widget)
        
        if project.images:
            cols = 4
            for i, img_path in enumerate(project.images):
                frame = QFrame()
                frame.setFrameStyle(QFrame.Shape.Box)
                frame_layout = QVBoxLayout(frame)
                
                img_label = QLabel()
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(150, 100, Qt.AspectRatioMode.KeepAspectRatio)
                    img_label.setPixmap(scaled)
                else:
                    img_label.setText("❌")
                frame_layout.addWidget(img_label)
                
                btn_regen = QPushButton(f"🔄 #{i+1}")
                btn_regen.setProperty("index", i)
                btn_regen.clicked.connect(lambda checked, idx=i: self._request_regenerate(idx))
                frame_layout.addWidget(btn_regen)
                
                self.images_grid.addWidget(frame, i // cols, i % cols)
        else:
            left_layout.addWidget(QLabel("Нет изображений"))
        
        scroll.setWidget(images_widget)
        left_layout.addWidget(scroll)
        splitter.addWidget(left)
        
        # Правая часть — параметры
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        # AI параметры
        params_group = QGroupBox("🤖 AI-подобранные параметры")
        params_layout = QFormLayout(params_group)
        params_layout.addRow("Стиль:", QLabel(project.ai_style or "—"))
        params_layout.addRow("Голос:", QLabel(project.ai_voice or "—"))
        params_layout.addRow("Изображения:", QLabel(project.ai_image_style[:50] + "..." if project.ai_image_style else "—"))
        params_layout.addRow("Музыка:", QLabel(project.ai_music_mood or "—"))
        params_layout.addRow("Переходы:", QLabel(", ".join(project.ai_transitions) if project.ai_transitions else "—"))
        right_layout.addWidget(params_group)
        
        # Сценарий
        script_group = QGroupBox("📝 Сценарий")
        script_layout = QVBoxLayout(script_group)
        self.script_edit = QTextEdit()
        self.script_edit.setText(project.script[:2000] + "..." if len(project.script) > 2000 else project.script)
        self.script_edit.setMaximumHeight(200)
        script_layout.addWidget(self.script_edit)
        
        words = len(project.script.split()) if project.script else 0
        script_layout.addWidget(QLabel(f"Слов: {words}"))
        right_layout.addWidget(script_group)
        
        # SEO
        seo_group = QGroupBox("🔍 SEO")
        seo_layout = QFormLayout(seo_group)
        seo_layout.addRow("Заголовок:", QLabel(project.seo_title or project.name))
        seo_layout.addRow("Теги:", QLabel(", ".join(project.seo_tags[:5]) + "..." if project.seo_tags else "—"))
        
        # Хештеги
        hashtags = getattr(project, 'seo_hashtags', [])
        seo_layout.addRow("Хештеги:", QLabel(" ".join(hashtags) if hashtags else "—"))
        
        # A/B заголовки
        alt_titles = getattr(project, 'seo_alt_titles', [])
        if alt_titles and len(alt_titles) > 1:
            seo_layout.addRow("A/B варианты:", QLabel(f"{len(alt_titles)} заголовков"))
        
        right_layout.addWidget(seo_group)
        
        # === ПРЕВЬЮ (THUMBNAILS) ===
        thumb_group = QGroupBox("🎨 Превью (Thumbnails)")
        thumb_layout = QVBoxLayout(thumb_group)
        
        # Показываем превью если есть
        if project.thumbnails:
            thumb_layout.addWidget(QLabel(f"✅ {len(project.thumbnails)} вариантов готово"))
            
            # Показываем промпты
            thumbnail_prompts = getattr(project, 'thumbnail_prompts', [])
            if thumbnail_prompts:
                for i, tp in enumerate(thumbnail_prompts, 1):
                    prompt_type = tp.get('type', f'variant_{i}')
                    why_viral = tp.get('why_viral', '')
                    
                    prompt_label = QLabel(f"#{i} {prompt_type.upper()}: {why_viral[:60]}...")
                    prompt_label.setStyleSheet("color: #14a3a8; font-size: 11px;")
                    prompt_label.setWordWrap(True)
                    thumb_layout.addWidget(prompt_label)
                
                # Кнопка для просмотра всех промптов
                btn_show_prompts = QPushButton("📋 Показать все промпты")
                btn_show_prompts.clicked.connect(lambda: self._show_thumbnail_prompts(project))
                thumb_layout.addWidget(btn_show_prompts)
            else:
                thumb_layout.addWidget(QLabel("Промпты не сохранены"))
        else:
            thumb_layout.addWidget(QLabel("Превью ещё не сгенерированы"))
        
        right_layout.addWidget(thumb_group)
        
        right_layout.addStretch()
        splitter.addWidget(right)
        
        splitter.setSizes([500, 400])
        layout.addWidget(splitter)
        
        # Кнопки
        btn_row = QHBoxLayout()
        
        btn_save = QPushButton("💾 Сохранить изменения")
        btn_save.clicked.connect(self._save_changes)
        btn_row.addWidget(btn_save)
        
        btn_quick_preview = QPushButton("👁 Быстрое превью")
        btn_quick_preview.setToolTip("Создать быстрое превью видео (720p, 30 сек)")
        btn_quick_preview.clicked.connect(self._create_quick_preview)
        btn_row.addWidget(btn_quick_preview)
        
        btn_render = QPushButton("🎬 Финальный рендер")
        btn_render.setStyleSheet("background: #4CAF50; padding: 10px;")
        btn_render.clicked.connect(self.accept)
        btn_row.addWidget(btn_render)
        
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)
        
        layout.addLayout(btn_row)
    
    def _create_quick_preview(self):
        """Создание быстрого превью видео"""
        if not self.project.images:
            QMessageBox.warning(self, "Ошибка", "Нет изображений для превью")
            return
        
        try:
            from core.video_editor import VideoEditor
            from pathlib import Path
            
            editor = VideoEditor()
            
            images = [Path(p) for p in self.project.images if Path(p).exists()]
            if not images:
                QMessageBox.warning(self, "Ошибка", "Изображения не найдены")
                return
            
            # Путь для превью
            output_dir = Path(self.project.images[0]).parent.parent
            preview_path = output_dir / f"{self.project.name}_preview.mp4"
            
            QMessageBox.information(
                self, "Превью",
                f"Создание быстрого превью...\nЭто займёт 30-60 секунд."
            )
            
            # Создаём превью
            audio_path = Path(self.project.audio_path) if self.project.audio_path else None
            
            editor.create_quick_preview(
                images=images,
                output_path=preview_path,
                audio_path=audio_path,
                duration_per_image=2.0,
                resolution=(1280, 720)
            )
            
            QMessageBox.information(
                self, "Готово!",
                f"Превью создано:\n{preview_path}\n\nОткрыть файл?"
            )
            
            # Открываем файл
            import subprocess
            subprocess.run(['open', str(preview_path)])
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать превью: {e}")
    
    def _get_status_style(self, status: str) -> str:
        colors = {
            "ready": "background: #4CAF50; color: white; padding: 5px; border-radius: 3px;",
            "completed": "background: #2196F3; color: white; padding: 5px; border-radius: 3px;",
            "error": "background: #f44336; color: white; padding: 5px; border-radius: 3px;",
        }
        return colors.get(status, "background: #666; color: white; padding: 5px; border-radius: 3px;")
    
    def _request_regenerate(self, index: int):
        QMessageBox.information(self, "Перегенерация", f"Запрос на перегенерацию изображения #{index + 1}")
    
    def _save_changes(self):
        QMessageBox.information(self, "Сохранено", "Изменения сохранены")
    
    def _show_thumbnail_prompts(self, project):
        """Показать все промпты для превью"""
        thumbnail_prompts = getattr(project, 'thumbnail_prompts', [])
        
        if not thumbnail_prompts:
            QMessageBox.information(self, "Промпты", "Промпты не найдены")
            return
        
        # Создаём диалог с промптами
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Промпты превью: {project.name}")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        info = QLabel("📋 Скопируйте промпт и измените для перегенерации в любом AI генераторе")
        info.setStyleSheet("color: #14a3a8; padding: 10px; background: #1a3a3a; border-radius: 5px;")
        layout.addWidget(info)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        for i, tp in enumerate(thumbnail_prompts, 1):
            group = QGroupBox(f"#{i} {tp.get('type', 'variant').upper()}")
            group_layout = QVBoxLayout(group)
            
            # Почему вирусный
            why_label = QLabel(f"🎯 Почему вирусный: {tp.get('why_viral', '—')}")
            why_label.setWordWrap(True)
            why_label.setStyleSheet("color: #4CAF50;")
            group_layout.addWidget(why_label)
            
            # Промпт
            prompt_edit = QTextEdit()
            prompt_edit.setText(tp.get('prompt', ''))
            prompt_edit.setMaximumHeight(100)
            prompt_edit.setReadOnly(True)
            group_layout.addWidget(prompt_edit)
            
            # Кнопка копирования
            btn_copy = QPushButton("📋 Копировать промпт")
            btn_copy.clicked.connect(lambda checked, text=tp.get('prompt', ''): self._copy_to_clipboard(text))
            group_layout.addWidget(btn_copy)
            
            # Путь к файлу
            if tp.get('path'):
                path_label = QLabel(f"📁 {tp.get('path')}")
                path_label.setStyleSheet("color: #888; font-size: 10px;")
                group_layout.addWidget(path_label)
            
            content_layout.addWidget(group)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec()
    
    def _copy_to_clipboard(self, text: str):
        """Копирование в буфер обмена"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Скопировано", "Промпт скопирован в буфер обмена!")


class QueueTab(QWidget):
    """Вкладка очереди проектов с поддержкой профилей каналов"""
    
    def __init__(self):
        super().__init__()
        self.pipeline = None
        self.style_manager = None
        self.worker = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_table)
        self.init_ui()
        self._init_pipeline()
    
    def _init_pipeline(self):
        """Инициализация пайплайна и менеджера стилей"""
        from core.smart_pipeline import SmartPipeline
        from core.channel_style import ChannelStyleManager
        self.pipeline = SmartPipeline(OUTPUT_DIR)
        self.style_manager = ChannelStyleManager()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # === ВЕРХНЯЯ ПАНЕЛЬ ===
        top_row = QHBoxLayout()
        
        btn_new = QPushButton("➕ Новый проект")
        btn_new.clicked.connect(self._add_project)
        btn_new.setStyleSheet("background: #14a3a8; padding: 10px;")
        top_row.addWidget(btn_new)
        
        btn_batch = QPushButton("📋 Добавить пакет")
        btn_batch.clicked.connect(self._add_batch)
        top_row.addWidget(btn_batch)
        
        top_row.addStretch()
        
        self.btn_start = QPushButton("▶️ Запустить очередь")
        self.btn_start.clicked.connect(self._start_queue)
        self.btn_start.setStyleSheet("background: #4CAF50; padding: 10px;")
        top_row.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹ Остановить")
        self.btn_stop.clicked.connect(self._stop_queue)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background: #e63946; padding: 10px;")
        top_row.addWidget(self.btn_stop)
        
        layout.addLayout(top_row)
        
        # === СТАТУС ===
        status_row = QHBoxLayout()
        self.queue_status = QLabel("Очередь: 0 проектов")
        self.queue_status.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_row.addWidget(self.queue_status)
        
        self.current_status = QLabel("")
        self.current_status.setStyleSheet("color: #14a3a8;")
        status_row.addWidget(self.current_status)
        status_row.addStretch()
        layout.addLayout(status_row)
        
        # === ТАБЛИЦА ПРОЕКТОВ ===
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Название", "Тема", "Длительность", "Статус", "Прогресс", "Действия", ""
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table)
        
        # === ГОТОВЫЕ ПРОЕКТЫ ===
        ready_group = QGroupBox("✅ Готовые к проверке")
        ready_layout = QVBoxLayout(ready_group)
        
        self.ready_list = QListWidget()
        self.ready_list.itemDoubleClicked.connect(self._preview_project)
        ready_layout.addWidget(self.ready_list)
        
        ready_btn_row = QHBoxLayout()
        btn_preview = QPushButton("👁 Просмотр")
        btn_preview.clicked.connect(self._preview_selected)
        ready_btn_row.addWidget(btn_preview)
        
        btn_render_all = QPushButton("🎬 Рендер всех")
        btn_render_all.clicked.connect(self._render_all_ready)
        btn_render_all.setStyleSheet("background: #4CAF50;")
        ready_btn_row.addWidget(btn_render_all)
        ready_layout.addLayout(ready_btn_row)
        
        layout.addWidget(ready_group)
        
        # Загружаем существующие проекты
        self._refresh_table()
    
    def _add_project(self):
        """Добавление нового проекта с поддержкой профилей"""
        # Получаем список профилей каналов
        channel_styles = self.style_manager.get_all_styles() if self.style_manager else []
        
        dialog = NewProjectDialog(channel_styles, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['name'] or not data['topic']:
                QMessageBox.warning(self, "Ошибка", "Заполните название и тему")
                return
            
            # Создаём проект
            project = self.pipeline.create_project(
                name=data['name'],
                topic=data['topic'],
                competitor_channel=data['competitor'],
                duration=data['duration'],
                language=data['language']
            )
            
            # Если выбран профиль канала — применяем его настройки
            if data.get('channel_style_id'):
                project.channel_style_id = data['channel_style_id']
                self.style_manager.apply_style_to_project(data['channel_style_id'], project)
                self.pipeline._save_projects()
            
            self.pipeline.add_to_queue(project.id)
            self._refresh_table()
            
            msg = f"Проект '{data['name']}' добавлен в очередь"
            if data.get('channel_style_id'):
                msg += "\n\n✅ Применён профиль канала (голос, стиль, эффекты)"
            QMessageBox.information(self, "Добавлено", msg)
    
    def _add_batch(self):
        """Добавление пакета проектов — несколько тем сразу!"""
        channel_styles = self.style_manager.get_all_styles() if self.style_manager else []
        
        dialog = BatchProjectsDialog(channel_styles, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            projects_data = dialog.get_projects()
            
            if not projects_data:
                QMessageBox.warning(self, "Ошибка", "Не указано ни одной темы")
                return
            
            added = 0
            for data in projects_data:
                # Создаём проект
                project = self.pipeline.create_project(
                    name=data['name'],
                    topic=data['topic'],
                    competitor_channel="",
                    duration=data['duration'],
                    language=data['language']
                )
                
                # Применяем профиль если выбран
                if data.get('channel_style_id'):
                    project.channel_style_id = data['channel_style_id']
                    self.style_manager.apply_style_to_project(data['channel_style_id'], project)
                    self.pipeline._save_projects()
                
                self.pipeline.add_to_queue(project.id)
                added += 1
            
            self._refresh_table()
            
            QMessageBox.information(
                self, "✅ Добавлено",
                f"Добавлено {added} проектов в очередь!\n\n"
                f"Нажмите '▶️ Запустить очередь' чтобы начать обработку.\n"
                f"Можете уйти — программа будет работать в фоне."
            )
    
    def _start_queue(self):
        """Запуск обработки очереди"""
        if not self.pipeline.queue:
            QMessageBox.warning(self, "Ошибка", "Очередь пуста")
            return
        
        reply = QMessageBox.question(
            self, "Запуск очереди",
            f"Запустить обработку {len(self.pipeline.queue)} проектов?\n\n"
            "Процесс будет работать в фоне.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            
            self.worker = QueueWorker(self.pipeline)
            self.worker.finished.connect(self._on_queue_finished)
            self.worker.error.connect(self._on_queue_error)
            self.worker.start()
            
            self.update_timer.start(2000)  # Обновление каждые 2 сек
    
    def _stop_queue(self):
        """Остановка очереди"""
        self.pipeline.stop_queue()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.update_timer.stop()
    
    def _on_queue_finished(self):
        """Очередь завершена"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.update_timer.stop()
        self._refresh_table()
        
        ready_count = len(self.pipeline.get_ready_projects())
        if ready_count > 0:
            QMessageBox.information(
                self, "Очередь завершена",
                f"Готово к проверке: {ready_count} проектов"
            )
    
    def _on_queue_error(self, error: str):
        """Ошибка очереди"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.update_timer.stop()
        QMessageBox.critical(self, "Ошибка", error)
    
    def _refresh_table(self):
        """Обновление таблицы проектов"""
        if not self.pipeline:
            return
        
        projects = self.pipeline.get_all_projects()
        self.table.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            self.table.setItem(row, 0, QTableWidgetItem(project.name))
            self.table.setItem(row, 1, QTableWidgetItem(project.topic[:50] + "..." if len(project.topic) > 50 else project.topic))
            self.table.setItem(row, 2, QTableWidgetItem(project.duration))
            
            status_item = QTableWidgetItem(self._translate_status(project.status))
            status_item.setBackground(self._get_status_color(project.status))
            self.table.setItem(row, 3, status_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(f"{project.progress}%"))
            
            # Кнопки действий
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            if project.status == "ready":
                btn_view = QPushButton("👁")
                btn_view.setToolTip("Просмотр")
                btn_view.clicked.connect(lambda checked, pid=project.id: self._preview_project_by_id(pid))
                btn_layout.addWidget(btn_view)
            
            btn_del = QPushButton("🗑")
            btn_del.setToolTip("Удалить")
            btn_del.clicked.connect(lambda checked, pid=project.id: self._delete_project(pid))
            btn_layout.addWidget(btn_del)
            
            self.table.setCellWidget(row, 5, btn_widget)
            
            # ID для ссылки
            id_item = QTableWidgetItem(project.id)
            id_item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.table.setItem(row, 6, id_item)
        
        # Обновляем список готовых
        self._update_ready_list()
        
        # Обновляем статус
        queue_len = len(self.pipeline.queue)
        self.queue_status.setText(f"Очередь: {queue_len} проектов | Всего: {len(projects)}")
        
        if self.pipeline.current_project_id:
            current = self.pipeline.get_project(self.pipeline.current_project_id)
            if current:
                self.current_status.setText(f"⏳ {current.name}: {current.current_step}")
    
    def _update_table(self):
        """Периодическое обновление таблицы"""
        self._refresh_table()
    
    def _update_ready_list(self):
        """Обновление списка готовых проектов"""
        self.ready_list.clear()
        for project in self.pipeline.get_ready_projects():
            item = QListWidgetItem(f"✅ {project.name}")
            item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.ready_list.addItem(item)
    
    def _translate_status(self, status: str) -> str:
        """Перевод статуса"""
        translations = {
            "queued": "В очереди",
            "analyzing": "Анализ...",
            "scripting": "Сценарий...",
            "generating_images": "Изображения...",
            "generating_voice": "Озвучка...",
            "assembling": "Сборка...",
            "ready": "✅ Готов",
            "rendering": "Рендер...",
            "completed": "✅ Завершён",
            "error": "❌ Ошибка",
            "paused": "⏸ Пауза"
        }
        return translations.get(status, status)
    
    def _get_status_color(self, status: str) -> QColor:
        """Цвет статуса"""
        colors = {
            "queued": QColor(100, 100, 100),
            "analyzing": QColor(255, 193, 7),
            "scripting": QColor(255, 193, 7),
            "generating_images": QColor(33, 150, 243),
            "generating_voice": QColor(33, 150, 243),
            "assembling": QColor(156, 39, 176),
            "ready": QColor(76, 175, 80),
            "completed": QColor(76, 175, 80),
            "error": QColor(244, 67, 54),
        }
        return colors.get(status, QColor(100, 100, 100))
    
    def _on_row_double_click(self, row: int, col: int):
        """Двойной клик по строке"""
        id_item = self.table.item(row, 6)
        if id_item:
            project_id = id_item.data(Qt.ItemDataRole.UserRole)
            self._preview_project_by_id(project_id)
    
    def _preview_project_by_id(self, project_id: str):
        """Просмотр проекта по ID"""
        project = self.pipeline.get_project(project_id)
        if project:
            dialog = ProjectPreviewDialog(project, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Запуск финального рендера
                self.pipeline.render_final(project_id)
                self._refresh_table()
    
    def _preview_project(self, item: QListWidgetItem):
        """Просмотр проекта из списка готовых"""
        project_id = item.data(Qt.ItemDataRole.UserRole)
        self._preview_project_by_id(project_id)
    
    def _preview_selected(self):
        """Просмотр выбранного проекта"""
        item = self.ready_list.currentItem()
        if item:
            self._preview_project(item)
    
    def _render_all_ready(self):
        """Рендер всех готовых проектов"""
        ready = self.pipeline.get_ready_projects()
        if not ready:
            QMessageBox.warning(self, "Ошибка", "Нет готовых проектов")
            return
        
        reply = QMessageBox.question(
            self, "Рендер всех",
            f"Запустить рендер {len(ready)} проектов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for project in ready:
                self.pipeline.render_final(project.id)
            self._refresh_table()
            QMessageBox.information(self, "Готово", "Рендер запущен")
    
    def _delete_project(self, project_id: str):
        """Удаление проекта"""
        reply = QMessageBox.question(
            self, "Удаление",
            "Удалить проект?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if project_id in self.pipeline.projects:
                del self.pipeline.projects[project_id]
            if project_id in self.pipeline.queue:
                self.pipeline.queue.remove(project_id)
            self.pipeline._save_projects()
            self._refresh_table()
    
    def add_batch_from_quickstart(self, data: dict):
        """
        Добавление проектов из вкладки Быстрый старт
        
        data = {
            'subniche': str,
            'subniche_data': dict,
            'voice_id': str,
            'voice_name': str,
            'style': str,
            'duration': str,
            'topics': list[dict],
            'channel_info': dict,
            'thumbnail_style': dict,
            'save_profile': bool
        }
        """
        if not data.get('topics'):
            return
        
        added = 0
        voice_name = data.get('voice_name', 'Brian')
        voice_id = data.get('voice_id', '')
        duration = data.get('duration', '20-30 минут')
        thumbnail_style = data.get('thumbnail_style', {})
        
        # Извлекаем чистое имя голоса
        if '(' in voice_name:
            voice_name = voice_name.split('(')[0].strip()
        voice_name = voice_name.lstrip(' ')
        
        for topic_data in data['topics']:
            title = topic_data.get('title', 'Без названия')
            description = topic_data.get('description', title)
            hook = topic_data.get('hook', '')
            
            # Создаём проект
            project = self.pipeline.create_project(
                name=title[:50],
                topic=f"{description}\n\nХук: {hook}" if hook else description,
                competitor_channel=data.get('channel_info', {}).get('url', ''),
                duration=duration,
                language="Русский"
            )
            
            # Применяем настройки из QuickStart
            project.ai_voice = voice_name
            project.ai_voice_id = voice_id
            project.ai_style = data.get('style', 'Документальный')
            project.ai_image_style = thumbnail_style.get('prompt_style', 'military history, WW2, documentary, cinematic, Kodachrome film')
            project.ai_music_mood = "dramatic, epic, orchestral"
            project.ai_transitions = ["fade", "zoom_in", "zoom_out", "pan"]
            
            # Сохраняем поднишу
            if data.get('subniche'):
                project.sub_niche = data['subniche']
            
            # SEO данные из канала конкурента
            channel_info = data.get('channel_info', {})
            if channel_info:
                project.competitor_channel = channel_info.get('url', '')
            
            self.pipeline._save_projects()
            self.pipeline.add_to_queue(project.id)
            added += 1
        
        self._refresh_table()
        
        # Показываем уведомление
        QMessageBox.information(
            self, "✅ Добавлено",
            f"Добавлено {added} проектов в очередь!\n\n"
            f"Подниша: {data.get('subniche', '—')}\n"
            f"Голос: {voice_name}\n\n"
            f"Нажмите '▶️ Запустить очередь' чтобы начать."
        )
