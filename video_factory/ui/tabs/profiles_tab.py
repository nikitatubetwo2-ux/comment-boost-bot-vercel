"""
Вкладка управления профилями каналов — запоминание стиля для каждого канала
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QSplitter, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import sys

sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from core.voice_library import VOICE_LIBRARY, VOICE_CATEGORIES, get_voice_by_id


class AnalyzeWorker(QThread):
    """Воркер для анализа канала"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, style_manager, style_id: str):
        super().__init__()
        self.style_manager = style_manager
        self.style_id = style_id
    
    def run(self):
        try:
            self.progress.emit("Анализ канала...")
            result = self.style_manager.analyze_and_setup(self.style_id)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SubnicheDialog(QDialog):
    """Диалог выбора подниши"""
    
    def __init__(self, subniches: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор подниши")
        self.setMinimumWidth(600)
        self.selected_subniche = None
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Выберите поднишу для канала:"))
        
        self.list = QListWidget()
        for sub in subniches:
            name = sub.get('name', 'Без названия')
            desc = sub.get('description', '')
            competition = sub.get('competition', 'средняя')
            potential = sub.get('potential', 'средний')
            
            item = QListWidgetItem(f"📌 {name}")
            item.setToolTip(f"{desc}\n\nКонкуренция: {competition}\nПотенциал: {potential}")
            item.setData(Qt.ItemDataRole.UserRole, sub)
            self.list.addItem(item)
        
        self.list.itemDoubleClicked.connect(self._on_select)
        layout.addWidget(self.list)
        
        # Детали выбранной подниши
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(100)
        layout.addWidget(self.details)
        
        self.list.currentItemChanged.connect(self._show_details)
        
        # Кнопки
        btn_row = QHBoxLayout()
        
        btn_reject = QPushButton("❌ Другие варианты")
        btn_reject.clicked.connect(self.reject)
        btn_row.addWidget(btn_reject)
        
        btn_select = QPushButton("✅ Выбрать")
        btn_select.clicked.connect(self._on_select)
        btn_select.setStyleSheet("background: #4CAF50;")
        btn_row.addWidget(btn_select)
        
        layout.addLayout(btn_row)
    
    def _show_details(self, item):
        if item:
            sub = item.data(Qt.ItemDataRole.UserRole)
            topics = sub.get('example_topics', [])
            self.details.setText(
                f"📝 {sub.get('description', '')}\n\n"
                f"Примеры тем:\n" + "\n".join(f"• {t}" for t in topics[:3])
            )
    
    def _on_select(self):
        item = self.list.currentItem()
        if item:
            self.selected_subniche = item.data(Qt.ItemDataRole.UserRole)
            self.accept()


class ProfilesTab(QWidget):
    """Вкладка управления профилями каналов"""
    
    profile_selected = pyqtSignal(object)  # Сигнал при выборе профиля
    
    def __init__(self):
        super().__init__()
        self.style_manager = None
        self.current_style = None
        self.worker = None
        self.init_ui()
        self._init_manager()
    
    def _init_manager(self):
        """Инициализация менеджера стилей"""
        from core.channel_style import ChannelStyleManager
        self.style_manager = ChannelStyleManager()
        self._refresh_list()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # === ЛЕВАЯ ПАНЕЛЬ — СПИСОК ПРОФИЛЕЙ ===
        left = QWidget()
        left.setMaximumWidth(300)
        left_layout = QVBoxLayout(left)
        
        left_layout.addWidget(QLabel("📺 Профили каналов"))
        
        # Кнопки
        btn_row = QHBoxLayout()
        btn_new = QPushButton("➕ Новый")
        btn_new.clicked.connect(self._create_profile)
        btn_row.addWidget(btn_new)
        
        btn_del = QPushButton("🗑")
        btn_del.clicked.connect(self._delete_profile)
        btn_row.addWidget(btn_del)
        left_layout.addLayout(btn_row)
        
        # Список
        self.profiles_list = QListWidget()
        self.profiles_list.currentItemChanged.connect(self._on_profile_selected)
        left_layout.addWidget(self.profiles_list)
        
        layout.addWidget(left)
        
        # === ПРАВАЯ ПАНЕЛЬ — ДЕТАЛИ ПРОФИЛЯ ===
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        # Заголовок
        self.profile_title = QLabel("Выберите профиль")
        self.profile_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        right_layout.addWidget(self.profile_title)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #14a3a8;")
        right_layout.addWidget(self.status_label)
        
        # Скролл для деталей
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        details_widget = QWidget()
        self.details_layout = QVBoxLayout(details_widget)
        
        # Конкурент
        competitor_group = QGroupBox("🎯 Конкурент для копирования")
        competitor_layout = QFormLayout(competitor_group)
        
        self.competitor_edit = QLineEdit()
        self.competitor_edit.setPlaceholderText("@channel или URL")
        competitor_layout.addRow("Канал:", self.competitor_edit)
        
        self.competitor_name = QLabel("—")
        competitor_layout.addRow("Название:", self.competitor_name)
        
        btn_analyze = QPushButton("🔍 Анализировать и настроить")
        btn_analyze.clicked.connect(self._analyze_competitor)
        btn_analyze.setStyleSheet("background: #14a3a8; padding: 8px;")
        competitor_layout.addRow(btn_analyze)
        
        self.details_layout.addWidget(competitor_group)
        
        # Подниша
        niche_group = QGroupBox("📌 Подниша")
        niche_layout = QFormLayout(niche_group)
        
        self.main_niche = QLabel("—")
        niche_layout.addRow("Основная ниша:", self.main_niche)
        
        self.sub_niche = QLabel("—")
        self.sub_niche.setWordWrap(True)
        niche_layout.addRow("Подниша:", self.sub_niche)
        
        btn_change_niche = QPushButton("🔄 Сменить поднишу")
        btn_change_niche.clicked.connect(self._change_subniche)
        niche_layout.addRow(btn_change_niche)
        
        self.details_layout.addWidget(niche_group)
        
        # Стиль
        style_group = QGroupBox("🎨 Стиль контента")
        style_layout = QFormLayout(style_group)
        
        self.narrative_style = QLabel("—")
        style_layout.addRow("Повествование:", self.narrative_style)
        
        self.tone = QLabel("—")
        style_layout.addRow("Тон:", self.tone)
        
        self.image_style = QLabel("—")
        self.image_style.setWordWrap(True)
        style_layout.addRow("Изображения:", self.image_style)
        
        self.details_layout.addWidget(style_group)
        
        # Голос
        voice_group = QGroupBox("🎙 Голос")
        voice_layout = QFormLayout(voice_group)
        
        self.voice_name = QLabel("—")
        voice_layout.addRow("Голос:", self.voice_name)
        
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(280)
        self._populate_voice_combo()
        self.voice_combo.currentTextChanged.connect(self._on_voice_changed)
        voice_layout.addRow("Изменить:", self.voice_combo)
        
        # Описание голоса
        self.voice_desc = QLabel("")
        self.voice_desc.setStyleSheet("color: #888; font-size: 10px;")
        self.voice_desc.setWordWrap(True)
        voice_layout.addRow("", self.voice_desc)
        self.voice_combo.currentIndexChanged.connect(self._update_voice_desc)
        
        self.details_layout.addWidget(voice_group)
        
        # Музыка
        music_group = QGroupBox("🎵 Музыка")
        music_layout = QFormLayout(music_group)
        
        self.music_mood = QLabel("—")
        music_layout.addRow("Настроение:", self.music_mood)
        
        self.details_layout.addWidget(music_group)
        
        # Статистика
        stats_group = QGroupBox("📊 Статистика")
        stats_layout = QFormLayout(stats_group)
        
        self.videos_count = QLabel("0")
        stats_layout.addRow("Видео создано:", self.videos_count)
        
        self.details_layout.addWidget(stats_group)
        
        self.details_layout.addStretch()
        
        scroll.setWidget(details_widget)
        right_layout.addWidget(scroll)
        
        # Кнопки действий
        action_row = QHBoxLayout()
        
        btn_topics = QPushButton("💡 Сгенерировать темы")
        btn_topics.clicked.connect(self._generate_topics)
        btn_topics.setStyleSheet("background: #e63946;")
        action_row.addWidget(btn_topics)
        
        btn_save = QPushButton("💾 Сохранить изменения")
        btn_save.clicked.connect(self._save_changes)
        action_row.addWidget(btn_save)
        
        right_layout.addLayout(action_row)
        
        layout.addWidget(right)
    
    def _refresh_list(self):
        """Обновление списка профилей"""
        self.profiles_list.clear()
        if not self.style_manager:
            return
        
        for style in self.style_manager.get_all_styles():
            item = QListWidgetItem(f"📺 {style.name}")
            item.setData(Qt.ItemDataRole.UserRole, style.id)
            if style.sub_niche:
                item.setToolTip(f"Подниша: {style.sub_niche}")
            self.profiles_list.addItem(item)
    
    def _create_profile(self):
        """Создание нового профиля"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Новый профиль", "Название канала:")
        if ok and name:
            style = self.style_manager.create_style(name)
            self._refresh_list()
            
            # Выбираем созданный профиль
            for i in range(self.profiles_list.count()):
                item = self.profiles_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == style.id:
                    self.profiles_list.setCurrentItem(item)
                    break
    
    def _delete_profile(self):
        """Удаление профиля"""
        item = self.profiles_list.currentItem()
        if not item:
            return
        
        reply = QMessageBox.question(
            self, "Удаление",
            "Удалить профиль? Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            style_id = item.data(Qt.ItemDataRole.UserRole)
            self.style_manager.delete_style(style_id)
            self._refresh_list()
            self.current_style = None
            self.profile_title.setText("Выберите профиль")
    
    def _on_profile_selected(self, item):
        """При выборе профиля"""
        if not item:
            return
        
        style_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_style = self.style_manager.get_style(style_id)
        
        if self.current_style:
            self._update_details()
    
    def _update_details(self):
        """Обновление деталей профиля"""
        s = self.current_style
        if not s:
            return
        
        self.profile_title.setText(f"📺 {s.name}")
        
        self.competitor_edit.setText(s.competitor_channel)
        self.competitor_name.setText(s.competitor_name or "—")
        
        self.main_niche.setText(s.main_niche or "—")
        self.sub_niche.setText(f"{s.sub_niche}\n{s.sub_niche_description}" if s.sub_niche else "—")
        
        self.narrative_style.setText(s.narrative_style or "—")
        self.tone.setText(s.tone or "—")
        self.image_style.setText(s.image_style[:60] + "..." if s.image_style and len(s.image_style) > 60 else s.image_style or "—")
        
        self.voice_name.setText(s.voice_name or "—")
        self.music_mood.setText(s.music_mood or "—")
        self.videos_count.setText(str(s.videos_created))
    
    def _analyze_competitor(self):
        """Анализ конкурента"""
        if not self.current_style:
            return
        
        competitor = self.competitor_edit.text().strip()
        if not competitor:
            QMessageBox.warning(self, "Ошибка", "Введите канал конкурента")
            return
        
        # Сохраняем канал
        self.style_manager.update_style(self.current_style.id, competitor_channel=competitor)
        
        self.status_label.setText("🔄 Анализ канала...")
        
        self.worker = AnalyzeWorker(self.style_manager, self.current_style.id)
        self.worker.progress.connect(lambda m: self.status_label.setText(m))
        self.worker.finished.connect(self._on_analysis_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()
    
    def _on_analysis_done(self, result: dict):
        """Анализ завершён"""
        if "error" in result:
            self.status_label.setText(f"❌ {result['error']}")
            return
        
        self.status_label.setText("✅ Анализ завершён")
        
        # Обновляем текущий стиль
        self.current_style = self.style_manager.get_style(self.current_style.id)
        self._update_details()
        
        # Показываем диалог выбора подниши
        niche_analysis = result.get('niche_analysis', {})
        subniches = niche_analysis.get('subniches', [])
        
        if subniches:
            dialog = SubnicheDialog(subniches, self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_subniche:
                sub = dialog.selected_subniche
                self.style_manager.select_subniche(
                    self.current_style.id,
                    sub.get('name', ''),
                    sub.get('description', '')
                )
                self.current_style = self.style_manager.get_style(self.current_style.id)
                self._update_details()
                QMessageBox.information(self, "Готово", f"Подниша выбрана: {sub.get('name')}")
    
    def _change_subniche(self):
        """Смена подниши"""
        if not self.current_style:
            return
        
        # Генерируем новые подниши (исключая отклонённые)
        from core.groq_client import GroqClient
        from config import config
        
        if not config.api.groq_key:
            QMessageBox.warning(self, "Ошибка", "Groq API ключ не настроен")
            return
        
        self.status_label.setText("🔄 Генерация новых подниш...")
        
        groq = GroqClient(config.api.groq_key, config.api.groq_model)
        
        # Добавляем текущую поднишу в отклонённые
        if self.current_style.sub_niche:
            self.style_manager.reject_subniche(self.current_style.id, self.current_style.sub_niche)
        
        subniches = groq.generate_more_subniches(
            self.current_style.main_niche,
            self.current_style.rejected_subniches,
            f"Канал: {self.current_style.name}, Стиль: {self.current_style.narrative_style}"
        )
        
        self.status_label.setText("")
        
        if subniches:
            dialog = SubnicheDialog(subniches, self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_subniche:
                sub = dialog.selected_subniche
                self.style_manager.select_subniche(
                    self.current_style.id,
                    sub.get('name', ''),
                    sub.get('description', '')
                )
                self.current_style = self.style_manager.get_style(self.current_style.id)
                self._update_details()
    
    def _populate_voice_combo(self):
        """Заполнение комбобокса голосами по категориям"""
        self.voice_combo.clear()
        
        for category_id, category_info in VOICE_CATEGORIES.items():
            self.voice_combo.addItem(f"━━━ {category_info['name']} ━━━", None)
            
            added_voices = set()
            for voice in VOICE_LIBRARY.values():
                if voice.name in category_info["voices"] and voice.name not in added_voices:
                    display = f"  {voice.name} ({voice.gender}, {voice.accent})"
                    self.voice_combo.addItem(display, voice.voice_id)
                    added_voices.add(voice.name)
    
    def _update_voice_desc(self, index: int):
        """Обновление описания голоса"""
        voice_id = self.voice_combo.currentData()
        if voice_id:
            voice = get_voice_by_id(voice_id)
            if voice:
                self.voice_desc.setText(f"💡 {voice.description}")
            else:
                self.voice_desc.setText("")
        else:
            self.voice_desc.setText("")
    
    def _on_voice_changed(self, voice_name: str):
        """При смене голоса"""
        if not self.current_style:
            return
        
        voice_id = self.voice_combo.currentData()
        if not voice_id:  # Это заголовок категории
            return
        
        self.style_manager.update_style(
            self.current_style.id,
            voice_name=voice_name.strip(),
            voice_id=voice_id
        )
    
    def _generate_topics(self):
        """Генерация тем для канала"""
        if not self.current_style:
            return
        
        if not self.current_style.sub_niche:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите поднишу")
            return
        
        self.status_label.setText("🔄 Генерация тем...")
        
        topics = self.style_manager.generate_topics(self.current_style.id, count=5)
        
        self.status_label.setText("")
        
        if topics:
            # Показываем темы
            text = "Сгенерированные темы:\n\n"
            for i, t in enumerate(topics, 1):
                title = t.get('title', 'Без названия')
                potential = t.get('viral_potential', '?')
                text += f"{i}. {title}\n   Потенциал: {potential}/10\n\n"
            
            QMessageBox.information(self, "Темы для видео", text)
    
    def _save_changes(self):
        """Сохранение изменений"""
        if not self.current_style:
            return
        
        self.style_manager.update_style(
            self.current_style.id,
            competitor_channel=self.competitor_edit.text().strip()
        )
        
        QMessageBox.information(self, "Сохранено", "Изменения сохранены")
    
    def _on_error(self, msg: str):
        """Обработка ошибки"""
        self.status_label.setText(f"❌ Ошибка")
        QMessageBox.critical(self, "Ошибка", msg)
