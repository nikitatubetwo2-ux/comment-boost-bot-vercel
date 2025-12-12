"""
Вкладка генерации сценариев
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QListWidget, QSpinBox, QSplitter,
    QListWidgetItem, QMessageBox, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config import config, PROFILES_DIR
from core.channel_profile import ProfileManager, ChannelProfile


class ScriptWorker(QThread):
    """Фоновый поток для генерации"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, task_type: str, data: dict):
        super().__init__()
        self.task_type = task_type
        self.data = data
    
    def run(self):
        try:
            from core.groq_client import GroqClient
            
            if not config.api.groq_key:
                self.error.emit("Groq API ключ не настроен!")
                return
            
            groq = GroqClient(config.api.groq_key, config.api.groq_model)
            
            if self.task_type == "subniche":
                self._generate_subniche(groq)
            elif self.task_type == "topics":
                self._generate_topics(groq)
            elif self.task_type == "script":
                self._generate_script(groq)
                
        except Exception as e:
            self.error.emit(str(e))
    
    def _generate_subniche(self, groq):
        self.progress.emit("Генерация подниши...")
        
        result = groq.generate_subniche(
            self.data['topic'],
            self.data.get('style_info', '')
        )
        
        self.finished.emit({'type': 'subniche', 'data': result})
    
    def _generate_topics(self, groq):
        self.progress.emit("Генерация тем...")
        
        topics = groq.generate_video_topics(
            self.data['subniche'],
            self.data.get('style_info', ''),
            count=5
        )
        
        self.finished.emit({'type': 'topics', 'data': topics})
    
    def _generate_script(self, groq):
        self.progress.emit("Генерация сценария (это может занять минуту)...")
        
        script = groq.generate_script(
            self.data['title'],
            self.data['duration'],
            self.data['style']
        )
        
        self.finished.emit({'type': 'script', 'data': script})


class ScriptTab(QWidget):
    """Вкладка для генерации сценариев"""
    
    # Сигнал для передачи данных в другие вкладки
    script_ready = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_profile = None
        self.current_subniche = ""
        self.worker = None
        self.init_ui()
        self.load_profiles()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Левая панель - настройки генерации
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Выбор профиля
        profile_group = QGroupBox("👤 Профиль канала")
        profile_layout = QVBoxLayout(profile_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(self.profile_combo)
        
        btn_refresh = QPushButton("🔄 Обновить список")
        btn_refresh.clicked.connect(self.load_profiles)
        profile_layout.addWidget(btn_refresh)
        
        # Информация о профиле
        self.profile_info = QLabel("Выберите профиль")
        self.profile_info.setWordWrap(True)
        self.profile_info.setStyleSheet("color: #888; font-size: 11px;")
        profile_layout.addWidget(self.profile_info)
        
        left_layout.addWidget(profile_group)
        
        # Генерация подниши
        niche_group = QGroupBox("🎯 Подниша")
        niche_layout = QVBoxLayout(niche_group)
        
        niche_layout.addWidget(QLabel("Основная тема:"))
        self.main_topic = QLineEdit()
        self.main_topic.setPlaceholderText("Например: корабли")
        niche_layout.addWidget(self.main_topic)
        
        btn_generate_niche = QPushButton("💡 Придумать поднишу")
        btn_generate_niche.clicked.connect(self.generate_subniche)
        niche_layout.addWidget(btn_generate_niche)
        
        self.subniche_result = QTextEdit()
        self.subniche_result.setMaximumHeight(100)
        self.subniche_result.setPlaceholderText("Сгенерированная подниша появится здесь...")
        niche_layout.addWidget(self.subniche_result)
        
        left_layout.addWidget(niche_group)
        
        # Генерация тем
        topics_group = QGroupBox("📋 Темы для видео")
        topics_layout = QVBoxLayout(topics_group)
        
        btn_generate_topics = QPushButton("🎲 Сгенерировать 5 тем")
        btn_generate_topics.clicked.connect(self.generate_topics)
        topics_layout.addWidget(btn_generate_topics)
        
        self.topics_list = QListWidget()
        self.topics_list.itemClicked.connect(self.on_topic_selected)
        topics_layout.addWidget(self.topics_list)
        
        left_layout.addWidget(topics_group)
        
        # Настройки сценария
        settings_group = QGroupBox("⚙️ Настройки сценария")
        settings_layout = QVBoxLayout(settings_group)
        
        # Длительность
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Длительность:"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "10-20 минут",
            "20-30 минут",
            "30-40 минут",
            "50-60 минут"
        ])
        duration_layout.addWidget(self.duration_combo)
        settings_layout.addLayout(duration_layout)
        
        # Стиль
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Стиль:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Документальный",
            "Развлекательный",
            "Образовательный",
            "Драматический"
        ])
        style_layout.addWidget(self.style_combo)
        settings_layout.addLayout(style_layout)
        
        left_layout.addWidget(settings_group)
        
        # Кнопка генерации
        btn_generate_script = QPushButton("📝 Сгенерировать сценарий")
        btn_generate_script.setStyleSheet("""
            QPushButton {
                background-color: #e63946;
                font-size: 16px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #ff4d5a;
            }
        """)
        btn_generate_script.clicked.connect(self.generate_script)
        left_layout.addWidget(btn_generate_script)
        
        # Прогресс
        self.progress_label = QLabel("")
        left_layout.addWidget(self.progress_label)
        
        left_layout.addStretch()
        
        # Правая панель - сценарий
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Заголовок
        title_group = QGroupBox("🎬 Заголовок видео")
        title_layout = QVBoxLayout(title_group)
        self.video_title = QLineEdit()
        self.video_title.setPlaceholderText("Введите или выберите тему...")
        title_layout.addWidget(self.video_title)
        right_layout.addWidget(title_group)
        
        # Сценарий
        script_group = QGroupBox("📜 Сценарий")
        script_layout = QVBoxLayout(script_group)
        
        self.script_text = QTextEdit()
        self.script_text.setPlaceholderText("Сценарий появится здесь после генерации...")
        script_layout.addWidget(self.script_text)
        
        # Статистика
        stats_layout = QHBoxLayout()
        self.word_count = QLabel("Слов: 0")
        self.estimated_time = QLabel("Примерное время: 0 мин")
        stats_layout.addWidget(self.word_count)
        stats_layout.addWidget(self.estimated_time)
        stats_layout.addStretch()
        script_layout.addLayout(stats_layout)
        
        right_layout.addWidget(script_group)
        
        # Кнопки
        actions_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self.save_script)
        actions_layout.addWidget(btn_save)
        
        btn_to_media = QPushButton("➡️ К генерации медиа")
        btn_to_media.clicked.connect(self.go_to_media)
        actions_layout.addWidget(btn_to_media)
        
        right_layout.addLayout(actions_layout)
        
        # Сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
    
    def load_profiles(self):
        """Загрузка списка профилей"""
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Выберите профиль --", None)
        
        pm = ProfileManager(PROFILES_DIR)
        profiles = pm.list_profiles()
        
        for p in profiles:
            self.profile_combo.addItem(
                f"{p['name']} ({p['niche']})",
                p['filepath']
            )
    
    def on_profile_changed(self, index):
        """Обработка выбора профиля"""
        filepath = self.profile_combo.currentData()
        
        if filepath:
            pm = ProfileManager(PROFILES_DIR)
            self.current_profile = pm.load_profile(Path(filepath))
            
            if self.current_profile:
                self.profile_info.setText(
                    f"Ниша: {self.current_profile.niche}\n"
                    f"Стиль: {self.current_profile.narrative_style}\n"
                    f"Тон: {self.current_profile.tone}"
                )
                self.main_topic.setText(self.current_profile.niche)
        else:
            self.current_profile = None
            self.profile_info.setText("Выберите профиль")
    
    def set_profile(self, profile: ChannelProfile):
        """Установка профиля из другой вкладки"""
        self.current_profile = profile
        self.load_profiles()
        
        # Находим и выбираем профиль в комбобоксе
        for i in range(self.profile_combo.count()):
            if profile.name in self.profile_combo.itemText(i):
                self.profile_combo.setCurrentIndex(i)
                break
    
    def get_style_info(self) -> str:
        """Получение информации о стиле"""
        if self.current_profile:
            return self.current_profile.get_style_summary()
        return ""
    
    def start_worker(self, task_type: str, data: dict):
        """Запуск фонового потока"""
        self.progress_label.setText("Загрузка...")
        
        self.worker = ScriptWorker(task_type, data)
        self.worker.progress.connect(lambda msg: self.progress_label.setText(msg))
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_error(self, message: str):
        self.progress_label.setText("")
        QMessageBox.critical(self, "Ошибка", message)
    
    def on_finished(self, result: dict):
        self.progress_label.setText("")
        result_type = result.get('type')
        
        if result_type == 'subniche':
            data = result['data']
            subniches = data.get('subniches', [])
            recommended = data.get('recommended', '')
            
            text = f"Рекомендация: {recommended}\n\n"
            for i, sub in enumerate(subniches, 1):
                text += f"{i}. {sub.get('name', '?')}\n"
                text += f"   {sub.get('description', '')}\n\n"
            
            self.subniche_result.setText(text)
            
            if subniches:
                self.current_subniche = subniches[0].get('name', '')
        
        elif result_type == 'topics':
            self.topics_list.clear()
            for topic in result['data']:
                title = topic.get('title', 'Без названия')
                potential = topic.get('viral_potential', 0)
                item = QListWidgetItem(f"🎬 [{potential}/10] {title}")
                item.setData(Qt.ItemDataRole.UserRole, topic)
                self.topics_list.addItem(item)
        
        elif result_type == 'script':
            script = result['data']
            self.script_text.setText(script)
            
            words = len(script.split())
            self.word_count.setText(f"Слов: {words}")
            minutes = words // 150
            self.estimated_time.setText(f"Примерное время: {minutes} мин")
    
    def generate_subniche(self):
        """Генерация подниши"""
        topic = self.main_topic.text().strip()
        if not topic:
            QMessageBox.warning(self, "Ошибка", "Введите основную тему")
            return
        
        self.start_worker("subniche", {
            'topic': topic,
            'style_info': self.get_style_info()
        })
    
    def generate_topics(self):
        """Генерация 5 тем"""
        subniche = self.current_subniche or self.main_topic.text().strip()
        if not subniche:
            QMessageBox.warning(self, "Ошибка", "Сначала введите тему или сгенерируйте поднишу")
            return
        
        self.start_worker("topics", {
            'subniche': subniche,
            'style_info': self.get_style_info()
        })
    
    def on_topic_selected(self, item):
        """Выбор темы"""
        topic_data = item.data(Qt.ItemDataRole.UserRole)
        if topic_data:
            self.video_title.setText(topic_data.get('title', ''))
    
    def generate_script(self):
        """Генерация сценария"""
        title = self.video_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок видео")
            return
        
        self.start_worker("script", {
            'title': title,
            'duration': self.duration_combo.currentText(),
            'style': self.style_combo.currentText()
        })
    
    def save_script(self):
        """Сохранение сценария"""
        script = self.script_text.toPlainText()
        if not script:
            QMessageBox.warning(self, "Ошибка", "Нет сценария для сохранения")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить сценарий", 
            f"{self.video_title.text()}.txt",
            "Text Files (*.txt)"
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Заголовок: {self.video_title.text()}\n")
                f.write(f"Длительность: {self.duration_combo.currentText()}\n")
                f.write(f"Стиль: {self.style_combo.currentText()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(script)
            
            QMessageBox.information(self, "Успех", "Сценарий сохранён!")
    
    def go_to_media(self):
        """Переход к генерации медиа"""
        script = self.script_text.toPlainText()
        title = self.video_title.text()
        
        if not script:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте сценарий")
            return
        
        # Передаём данные
        self.script_ready.emit({
            'title': title,
            'script': script,
            'duration': self.duration_combo.currentText(),
            'style': self.style_combo.currentText(),
            'profile': self.current_profile
        })
        
        QMessageBox.information(
            self, "Готово",
            "Данные переданы. Перейдите на вкладку 'Медиа'."
        )
