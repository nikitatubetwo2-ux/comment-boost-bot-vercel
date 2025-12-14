"""
Вкладка SEO оптимизации
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QListWidget, QProgressBar, QSplitter,
    QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config import config


class SEOWorker(QThread):
    """Фоновый поток для SEO"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, task_type: str, data: dict):
        super().__init__()
        self.task_type = task_type
        self.data = data
    
    def run(self):
        try:
            if self.task_type == "generate":
                self._generate_seo()
            elif self.task_type == "analyze":
                self._analyze_seo()
        except Exception as e:
            self.error.emit(str(e))
    
    def _generate_seo(self):
        from core.groq_client import GroqClient, get_groq_client
        
        if not config.api.groq_key:
            self.error.emit("Groq API ключ не настроен!")
            return
        
        groq = get_groq_client()
        
        self.progress.emit("Генерация SEO...")
        
        result = groq.generate_seo(
            self.data['title'],
            self.data['script'],
            self.data.get('competitor_tags', [])
        )
        
        self.finished.emit({'type': 'generate', 'data': result})
    
    def _analyze_seo(self):
        from core.seo_optimizer import SEOOptimizer
        
        optimizer = SEOOptimizer()
        
        self.progress.emit("Анализ SEO...")
        
        result = optimizer.analyze_seo(
            self.data['title'],
            self.data['description'],
            self.data['tags']
        )
        
        self.finished.emit({'type': 'analyze', 'data': result})


class SEOTab(QWidget):
    """Вкладка SEO оптимизации"""
    
    def __init__(self):
        super().__init__()
        self.current_title = ""
        self.current_script = ""
        self.competitor_tags = []
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Левая панель - ввод данных
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Заголовок
        title_group = QGroupBox("🎬 Заголовок видео")
        title_layout = QVBoxLayout(title_group)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите заголовок видео...")
        self.title_input.textChanged.connect(self.on_title_changed)
        title_layout.addWidget(self.title_input)
        
        self.title_stats = QLabel("Символов: 0/100")
        self.title_stats.setStyleSheet("color: #888;")
        title_layout.addWidget(self.title_stats)
        
        left_layout.addWidget(title_group)
        
        # Описание
        desc_group = QGroupBox("📝 Описание")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Описание видео...")
        self.description_input.textChanged.connect(self.on_description_changed)
        desc_layout.addWidget(self.description_input)
        
        self.desc_stats = QLabel("Символов: 0/5000")
        self.desc_stats.setStyleSheet("color: #888;")
        desc_layout.addWidget(self.desc_stats)
        
        btn_generate_desc = QPushButton("🤖 Сгенерировать описание")
        btn_generate_desc.clicked.connect(self.generate_description)
        desc_layout.addWidget(btn_generate_desc)
        
        left_layout.addWidget(desc_group)
        
        # Теги
        tags_group = QGroupBox("🏷 Теги")
        tags_layout = QVBoxLayout(tags_group)
        
        self.tags_input = QTextEdit()
        self.tags_input.setMaximumHeight(100)
        self.tags_input.setPlaceholderText("Теги через запятую...")
        tags_layout.addWidget(self.tags_input)
        
        self.tags_stats = QLabel("Тегов: 0/30")
        self.tags_stats.setStyleSheet("color: #888;")
        tags_layout.addWidget(self.tags_stats)
        
        btn_generate_tags = QPushButton("🤖 Сгенерировать теги")
        btn_generate_tags.clicked.connect(self.generate_tags)
        tags_layout.addWidget(btn_generate_tags)
        
        left_layout.addWidget(tags_group)
        
        # Хештеги
        hashtags_group = QGroupBox("#️⃣ Хештеги")
        hashtags_layout = QVBoxLayout(hashtags_group)
        
        self.hashtags_input = QLineEdit()
        self.hashtags_input.setPlaceholderText("#тег1 #тег2 #тег3")
        hashtags_layout.addWidget(self.hashtags_input)
        
        left_layout.addWidget(hashtags_group)
        
        # Правая панель - анализ
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Оценка SEO
        score_group = QGroupBox("📊 Оценка SEO")
        score_layout = QVBoxLayout(score_group)
        
        self.seo_score = QLabel("--")
        self.seo_score.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #14a3a8;
        """)
        self.seo_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.seo_score)
        
        self.seo_grade = QLabel("Нажмите 'Анализировать'")
        self.seo_grade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.seo_grade)
        
        btn_analyze = QPushButton("🔍 Анализировать SEO")
        btn_analyze.clicked.connect(self.analyze_seo)
        score_layout.addWidget(btn_analyze)
        
        right_layout.addWidget(score_group)
        
        # Результаты анализа
        results_group = QGroupBox("📋 Результаты")
        results_layout = QVBoxLayout(results_group)
        
        self.good_points = QListWidget()
        self.good_points.setMaximumHeight(120)
        results_layout.addWidget(QLabel("✅ Хорошо:"))
        results_layout.addWidget(self.good_points)
        
        self.issues = QListWidget()
        self.issues.setMaximumHeight(120)
        results_layout.addWidget(QLabel("⚠️ Улучшить:"))
        results_layout.addWidget(self.issues)
        
        right_layout.addWidget(results_group)
        
        # Рекомендации
        tips_group = QGroupBox("💡 Рекомендации")
        tips_layout = QVBoxLayout(tips_group)
        
        self.tips_text = QTextEdit()
        self.tips_text.setReadOnly(True)
        self.tips_text.setText("""
• Заголовок: 50-70 символов оптимально
• Ключевое слово в начале заголовка
• Описание: минимум 200 символов
• Добавьте таймкоды (главы)
• 20-30 релевантных тегов
• 3-5 хештегов
• Призыв к действию в описании
        """)
        tips_layout.addWidget(self.tips_text)
        
        right_layout.addWidget(tips_group)
        
        # Прогресс
        self.progress_label = QLabel("")
        right_layout.addWidget(self.progress_label)
        
        # Сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
    
    def set_data(self, title: str, script: str, tags: list = None):
        """Установка данных из других вкладок"""
        self.current_title = title
        self.current_script = script
        self.competitor_tags = tags or []
        
        self.title_input.setText(title)
    
    def on_title_changed(self):
        """Обновление статистики заголовка"""
        length = len(self.title_input.text())
        color = "#28a745" if length <= 100 else "#dc3545"
        self.title_stats.setText(f"Символов: {length}/100")
        self.title_stats.setStyleSheet(f"color: {color};")
    
    def on_description_changed(self):
        """Обновление статистики описания"""
        length = len(self.description_input.toPlainText())
        color = "#28a745" if length <= 5000 else "#dc3545"
        self.desc_stats.setText(f"Символов: {length}/5000")
        self.desc_stats.setStyleSheet(f"color: {color};")
    
    def start_worker(self, task_type: str, data: dict):
        """Запуск фонового потока"""
        self.progress_label.setText("Загрузка...")
        
        self.worker = SEOWorker(task_type, data)
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
        
        if result_type == 'generate':
            data = result['data']
            
            # Описание
            if 'description' in data:
                self.description_input.setText(data['description'])
            
            # Теги
            if 'tags' in data:
                self.tags_input.setText(', '.join(data['tags']))
                self.tags_stats.setText(f"Тегов: {len(data['tags'])}/30")
            
            # Хештеги
            if 'hashtags' in data:
                self.hashtags_input.setText(' '.join(data['hashtags']))
        
        elif result_type == 'analyze':
            data = result['data']
            
            # Оценка
            score = data.get('score', 0)
            self.seo_score.setText(str(score))
            
            # Цвет по оценке
            if score >= 80:
                color = "#28a745"
            elif score >= 60:
                color = "#e6b800"
            else:
                color = "#dc3545"
            self.seo_score.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {color};")
            
            self.seo_grade.setText(data.get('grade', ''))
            
            # Хорошие моменты
            self.good_points.clear()
            for point in data.get('good_points', []):
                self.good_points.addItem(point)
            
            # Проблемы
            self.issues.clear()
            for issue in data.get('issues', []):
                self.issues.addItem(issue)
    
    def generate_description(self):
        """Генерация описания"""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок")
            return
        
        self.start_worker("generate", {
            'title': title,
            'script': self.current_script or title,
            'competitor_tags': self.competitor_tags
        })
    
    def generate_tags(self):
        """Генерация тегов"""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок")
            return
        
        self.start_worker("generate", {
            'title': title,
            'script': self.current_script or title,
            'competitor_tags': self.competitor_tags
        })
    
    def analyze_seo(self):
        """Анализ SEO"""
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        tags_text = self.tags_input.toPlainText().strip()
        
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок")
            return
        
        tags = [t.strip() for t in tags_text.split(',') if t.strip()]
        
        self.start_worker("analyze", {
            'title': title,
            'description': description,
            'tags': tags
        })
