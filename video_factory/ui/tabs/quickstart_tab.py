"""
Вкладка "Быстрый старт" — упрощённый процесс создания видео

WORKFLOW:
1. Вставил ссылку на канал-конкурент
2. AI анализирует и предлагает: поднишу, голос, стиль
3. Выбрал/изменил рекомендации
4. AI генерирует темы для видео
5. Выбрал темы → добавил в очередь
6. Профиль сохраняется для будущих генераций
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QListWidget, QProgressBar, QFrame,
    QListWidgetItem, QMessageBox, QScrollArea,
    QGridLayout, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])
from config import config


class AnalyzeWorker(QThread):
    """Фоновый анализ канала"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, channel_url: str):
        super().__init__()
        self.channel_url = channel_url
    
    def run(self):
        try:
            from core.youtube_analyzer import YouTubeAnalyzer
            from core.groq_client import GroqClient
            from core.voice_library import recommend_voice_for_content, VOICE_LIBRARY
            
            self.progress.emit("🔍 Анализирую канал...")
            
            analyzer = YouTubeAnalyzer(api_keys=config.api.youtube_keys)
            
            # Сначала извлекаем channel_id из URL
            channel_id = analyzer.extract_channel_id(self.channel_url)
            if not channel_id:
                self.error.emit("Не удалось извлечь ID канала из URL")
                return
            
            self.progress.emit(f"📡 Получаю информацию о канале...")
            channel = analyzer.get_channel_info(channel_id)

            if not channel:
                self.error.emit("Канал не найден")
                return
            
            self.progress.emit("📊 Получаю видео...")
            videos = analyzer.get_channel_videos(channel.channel_id, max_results=15)
            
            self.progress.emit("🧠 AI анализ стиля...")
            groq = GroqClient(config.api.groq_key, config.api.groq_model)
            
            titles = [v.title for v in videos]
            descriptions = [v.description for v in videos if v.description]
            
            # Анализ стиля
            style = groq.analyze_style(descriptions, titles)
            
            self.progress.emit("💡 Генерирую рекомендации...")
            
            # Генерация подниш
            main_topic = style.get('main_topic', channel.title)
            subniches = groq.generate_subniche(main_topic, f"Канал: {channel.title}, подписчиков: {channel.subscriber_count}")
            
            # Анализ голоса конкурента
            voice_analysis = groq.analyze_competitor_voice(channel.title, titles, descriptions)
            
            # Рекомендация голоса из библиотеки
            content_type = "military" if any(w in main_topic.lower() for w in ["война", "военн", "war", "military", "ww2"]) else "documentary"
            recommended_voice = recommend_voice_for_content(content_type, voice_analysis.get("gender", "male"))
            
            # Генерация тем
            if subniches.get('subniches'):
                best_subniche = subniches['subniches'][0]['name']
                topics = groq.generate_video_topics(best_subniche, str(style), count=5)
            else:
                topics = []
            
            # Анализ стиля превью
            thumbnail_style = groq.analyze_competitor_thumbnail_style(channel.title, titles)
            
            result = {
                'channel': {
                    'title': channel.title,
                    'subscribers': channel.subscriber_count,
                    'videos_count': channel.video_count,
                    'url': self.channel_url
                },
                'style': style,
                'subniches': subniches.get('subniches', []),
                'recommended_subniche': subniches.get('recommended', ''),
                'topics': topics,
                'voice_analysis': voice_analysis,
                'recommended_voice': recommended_voice,
                'thumbnail_style': thumbnail_style,
                'all_voices': list(VOICE_LIBRARY.values())
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")


class SubnicheWorker(QThread):
    """Фоновая генерация подниш"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, main_niche: str, rejected: list, style_context: str):
        super().__init__()
        self.main_niche = main_niche
        self.rejected = rejected
        self.style_context = style_context
    
    def run(self):
        try:
            from core.groq_client import GroqClient
            groq = GroqClient(config.api.groq_key, config.api.groq_model)
            subniches = groq.generate_more_subniches(self.main_niche, self.rejected, self.style_context)
            self.finished.emit(subniches)
        except Exception as e:
            self.error.emit(str(e))


class TopicsWorker(QThread):
    """Фоновая генерация тем"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, subniche: str, style_info: str, excluded: list, seed: int):
        super().__init__()
        self.subniche = subniche
        self.style_info = style_info
        self.excluded = excluded
        self.seed = seed
    
    def run(self):
        try:
            from core.groq_client import GroqClient
            groq = GroqClient(config.api.groq_key, config.api.groq_model)
            topics = groq.generate_video_topics(
                self.subniche, 
                self.style_info, 
                count=5,
                excluded_topics=self.excluded,
                variation_seed=self.seed
            )
            self.finished.emit(topics)
        except Exception as e:
            self.error.emit(str(e))


class QuickStartTab(QWidget):
    """
    Упрощённый процесс создания видео:
    1. Вставил ссылку на канал-конкурент
    2. Получил рекомендации (подниша, стиль, голос, темы)
    3. Выбрал/изменил что нужно
    4. Запустил генерацию
    5. Профиль сохраняется для будущего использования
    """
    
    start_generation = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.analysis_result = None
        self.worker = None
        self.subniche_worker = None
        self.topics_worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        # Заголовок
        header = QLabel("🚀 Быстрый старт")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #14a3a8;")
        content_layout.addWidget(header)
        
        desc = QLabel("Вставь ссылку на канал → получи рекомендации → выбери темы → запусти генерацию")
        desc.setStyleSheet("color: #888; margin-bottom: 10px;")
        content_layout.addWidget(desc)
        
        # === ШАГ 1: Ввод канала ===
        self._create_step1(content_layout)
        
        # === ШАГ 2: Рекомендации ===
        self._create_step2(content_layout)
        
        # === ШАГ 3: Темы ===
        self._create_step3(content_layout)
        
        # === ШАГ 4: Запуск ===
        self._create_step4(content_layout)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_step1(self, layout):
        """Шаг 1: Ввод канала"""
        step1 = QGroupBox("1️⃣ Канал-конкурент")
        step1_layout = QVBoxLayout(step1)
        
        input_layout = QHBoxLayout()
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Вставь ссылку на YouTube канал или @username")
        self.channel_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                background: #2d2d2d;
            }
            QLineEdit:focus { border-color: #14a3a8; }
        """)
        input_layout.addWidget(self.channel_input)
        
        self.btn_analyze = QPushButton("🔍 Анализировать")
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                background: #14a3a8;
                border: none;
                border-radius: 8px;
                color: white;
            }
            QPushButton:hover { background: #1abc9c; }
            QPushButton:disabled { background: #555; }
        """)
        self.btn_analyze.clicked.connect(self.start_analysis)
        input_layout.addWidget(self.btn_analyze)
        
        step1_layout.addLayout(input_layout)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #14a3a8;")
        step1_layout.addWidget(self.progress_label)
        
        layout.addWidget(step1)
    
    def _create_step2(self, layout):
        """Шаг 2: Рекомендации AI"""
        self.step2 = QGroupBox("2️⃣ Рекомендации AI (можно изменить)")
        self.step2.setVisible(False)
        step2_layout = QVBoxLayout(self.step2)
        step2_layout.setSpacing(10)
        step2_layout.setContentsMargins(10, 15, 10, 10)
        
        # Информация о канале
        self.channel_info = QLabel("")
        self.channel_info.setStyleSheet("color: #14a3a8; font-weight: bold; padding: 8px; background: #1a3a3a; border-radius: 5px;")
        self.channel_info.setWordWrap(True)
        self.channel_info.setMinimumHeight(30)
        step2_layout.addWidget(self.channel_info)
        
        # Подниша (МЕГА ВАЖНО)
        subniche_group = QGroupBox("📌 Подниша (ВАЖНО! На этом строится канал)")
        subniche_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        subniche_layout = QVBoxLayout(subniche_group)
        subniche_layout.setSpacing(8)
        
        sub_row = QHBoxLayout()
        sub_row.setSpacing(10)
        self.subniche_combo = QComboBox()
        self.subniche_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #14a3a8;
                border-radius: 6px;
                background: #2d2d2d;
                font-size: 13px;
                min-width: 350px;
                max-width: 500px;
            }
            QComboBox::drop-down { width: 30px; }
        """)
        self.subniche_combo.setSizePolicy(
            self.subniche_combo.sizePolicy().horizontalPolicy(),
            self.subniche_combo.sizePolicy().verticalPolicy()
        )
        sub_row.addWidget(self.subniche_combo, stretch=1)
        
        self.btn_more_subniches = QPushButton("🔄 Другие подниши")
        self.btn_more_subniches.setFixedWidth(150)
        self.btn_more_subniches.clicked.connect(self.generate_more_subniches)
        sub_row.addWidget(self.btn_more_subniches)
        subniche_layout.addLayout(sub_row)
        
        # Детальная информация о подниши
        self.subniche_details = QLabel("")
        self.subniche_details.setStyleSheet("""
            color: #ccc; 
            font-size: 12px; 
            padding: 10px; 
            background: #1a2a2a; 
            border-radius: 5px;
            border-left: 3px solid #14a3a8;
        """)
        self.subniche_details.setWordWrap(True)
        self.subniche_details.setMinimumHeight(60)
        subniche_layout.addWidget(self.subniche_details)
        
        # Метрики подниши
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(20)
        
        self.search_demand_label = QLabel("🔍 Спрос: —")
        self.search_demand_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.search_demand_label.setFixedWidth(120)
        metrics_row.addWidget(self.search_demand_label)
        
        self.competition_label = QLabel("⚔️ Конкуренция: —")
        self.competition_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        self.competition_label.setFixedWidth(150)
        metrics_row.addWidget(self.competition_label)
        
        self.viral_label = QLabel("🚀 Вирусность: —")
        self.viral_label.setStyleSheet("color: #E91E63; font-weight: bold;")
        self.viral_label.setFixedWidth(130)
        metrics_row.addWidget(self.viral_label)
        
        metrics_row.addStretch()
        subniche_layout.addLayout(metrics_row)
        
        step2_layout.addWidget(subniche_group)

        # Голос и стиль в одной строке
        voice_style_row = QHBoxLayout()
        voice_style_row.setSpacing(15)
        
        # Голос
        voice_group = QGroupBox("🎙 Голос озвучки")
        voice_layout = QVBoxLayout(voice_group)
        voice_layout.setSpacing(5)
        
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(280)
        self.voice_combo.setMaximumWidth(350)
        self.voice_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                background: #2d2d2d;
                font-size: 12px;
            }
        """)
        voice_layout.addWidget(self.voice_combo)
        
        self.voice_reason = QLabel("")
        self.voice_reason.setStyleSheet("color: #888; font-size: 10px;")
        self.voice_reason.setWordWrap(True)
        voice_layout.addWidget(self.voice_reason)
        
        voice_style_row.addWidget(voice_group)
        
        # Стиль контента
        style_group = QGroupBox("🎨 Стиль контента")
        style_layout = QVBoxLayout(style_group)
        
        self.style_label = QLabel("Документальный, драматичный")
        self.style_label.setStyleSheet("color: #14a3a8; font-weight: bold; padding: 8px;")
        self.style_label.setWordWrap(True)
        style_layout.addWidget(self.style_label)
        
        voice_style_row.addWidget(style_group)
        voice_style_row.addStretch()
        
        step2_layout.addLayout(voice_style_row)
        
        # Сохранить профиль
        self.save_profile_check = QCheckBox("💾 Сохранить как профиль канала (для будущих генераций)")
        self.save_profile_check.setChecked(True)
        self.save_profile_check.setStyleSheet("color: #14a3a8;")
        step2_layout.addWidget(self.save_profile_check)
        
        layout.addWidget(self.step2)
    
    def _create_step3(self, layout):
        """Шаг 3: Темы для видео"""
        self.step3 = QGroupBox("3️⃣ Темы для видео (выбери несколько)")
        self.step3.setVisible(False)
        step3_layout = QVBoxLayout(self.step3)
        
        self.topics_list = QListWidget()
        self.topics_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                background: #2d2d2d;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background: #14a3a8;
            }
            QListWidget::item:hover {
                background: #3a3a3a;
            }
        """)
        self.topics_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.topics_list.setMinimumHeight(200)
        step3_layout.addWidget(self.topics_list)
        
        topics_btn_layout = QHBoxLayout()
        self.btn_more_topics = QPushButton("🔄 Другие темы")
        self.btn_more_topics.clicked.connect(self.generate_more_topics)
        topics_btn_layout.addWidget(self.btn_more_topics)
        
        self.btn_select_all = QPushButton("✅ Выбрать все")
        self.btn_select_all.clicked.connect(self.select_all_topics)
        topics_btn_layout.addWidget(self.btn_select_all)
        
        self.topics_count = QLabel("Выбрано: 0")
        self.topics_count.setStyleSheet("color: #14a3a8; font-weight: bold;")
        topics_btn_layout.addWidget(self.topics_count)
        
        topics_btn_layout.addStretch()
        step3_layout.addLayout(topics_btn_layout)
        
        # Подключаем обновление счётчика
        self.topics_list.itemSelectionChanged.connect(self._update_topics_count)
        
        layout.addWidget(self.step3)

    def _create_step4(self, layout):
        """Шаг 4: Запуск генерации"""
        self.step4 = QGroupBox("4️⃣ Запуск генерации")
        self.step4.setVisible(False)
        step4_layout = QVBoxLayout(self.step4)
        step4_layout.setSpacing(10)
        
        # Настройки - первая строка
        options_layout1 = QHBoxLayout()
        options_layout1.setSpacing(15)
        
        dur_label = QLabel("⏱ Длительность:")
        dur_label.setFixedWidth(100)
        options_layout1.addWidget(dur_label)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "10-20 минут",
            "20-30 минут",
            "30-40 минут",
            "40-50 минут"
        ])
        self.duration_combo.setCurrentIndex(1)
        self.duration_combo.setFixedWidth(130)
        self.duration_combo.setStyleSheet("QComboBox { padding: 6px; }")
        options_layout1.addWidget(self.duration_combo)
        
        options_layout1.addSpacing(30)
        
        # Выбор языка контента
        lang_label = QLabel("🌍 Язык контента:")
        lang_label.setFixedWidth(110)
        options_layout1.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "🇷🇺 Русский",
            "🇺🇸 English",
            "🇪🇸 Español",
            "🇩🇪 Deutsch",
            "🇫🇷 Français",
            "🇵🇹 Português",
            "🇮🇹 Italiano"
        ])
        self.language_combo.setCurrentIndex(0)
        self.language_combo.setFixedWidth(130)
        self.language_combo.setStyleSheet("QComboBox { padding: 6px; }")
        self.language_combo.setToolTip("Язык на котором будет создан контент (сценарий, озвучка, SEO)")
        options_layout1.addWidget(self.language_combo)
        
        options_layout1.addStretch()
        step4_layout.addLayout(options_layout1)
        
        # Подсказка про язык
        lang_hint = QLabel("💡 Конкурент может быть на любом языке — контент создастся на выбранном")
        lang_hint.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 5px;")
        step4_layout.addWidget(lang_hint)
        
        # Информация о процессе
        info = QLabel(
            "📋 Что будет сделано автоматически:\n"
            "• Генерация сценария по теме\n"
            "• Генерация изображений (10-15 сек первые 5 мин, потом 40 сек)\n"
            "• Озвучка выбранным голосом\n"
            "• SEO оптимизация (теги, описание, хештеги)\n"
            "• Сборка видео → проверка → рендер"
        )
        info.setStyleSheet("color: #888; padding: 10px; background: #1a3a3a; border-radius: 5px;")
        step4_layout.addWidget(info)
        
        # Кнопка запуска
        self.btn_start = QPushButton("🚀 ДОБАВИТЬ В ОЧЕРЕДЬ И ЗАПУСТИТЬ")
        self.btn_start.setStyleSheet("""
            QPushButton {
                padding: 16px 32px;
                font-size: 16px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14a3a8, stop:1 #1abc9c);
                border: none;
                border-radius: 10px;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1abc9c, stop:1 #14a3a8);
            }
        """)
        self.btn_start.clicked.connect(self.start_generation_clicked)
        step4_layout.addWidget(self.btn_start)
        
        layout.addWidget(self.step4)
    
    def _update_topics_count(self):
        """Обновление счётчика выбранных тем"""
        count = len(self.topics_list.selectedItems())
        self.topics_count.setText(f"Выбрано: {count}")
    
    def start_analysis(self):
        """Запуск анализа канала"""
        url = self.channel_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите ссылку на канал")
            return
        
        self.btn_analyze.setEnabled(False)
        self.progress_label.setText("⏳ Анализирую канал...")
        
        self.worker = AnalyzeWorker(url)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, msg: str):
        self.progress_label.setText(msg)
    
    def on_error(self, error: str):
        self.btn_analyze.setEnabled(True)
        self.progress_label.setText(f"❌ Ошибка")
        QMessageBox.critical(self, "Ошибка", error)

    def on_analysis_complete(self, result: dict):
        """Обработка результатов анализа"""
        self.btn_analyze.setEnabled(True)
        self.progress_label.setText("✅ Анализ завершён!")
        self.analysis_result = result
        
        # Информация о канале
        channel = result.get('channel', {})
        self.channel_info.setText(
            f"📺 {channel.get('title', '')} | "
            f"👥 {channel.get('subscribers', 0):,} подписчиков | "
            f"🎬 {channel.get('videos_count', 0)} видео"
        )
        
        # Заполняем подниши
        self.subniche_combo.clear()
        subniches = result.get('subniches', [])
        for i, sub in enumerate(subniches):
            name = sub.get('name', str(sub))
            # Добавляем метрики в название
            search = sub.get('search_demand', {})
            comp = sub.get('competition', {})
            search_score = search.get('score', 0) if isinstance(search, dict) else 0
            comp_score = comp.get('score', 0) if isinstance(comp, dict) else 0
            
            display_name = f"{name}"
            if search_score and comp_score:
                display_name += f" (спрос: {search_score}, конкур: {comp_score})"
            
            self.subniche_combo.addItem(display_name, sub)
        
        # Подключаем обработчик и вызываем для первой подниши
        self.subniche_combo.currentIndexChanged.connect(self._on_subniche_changed)
        if subniches:
            self._on_subniche_changed(0)
        
        # Стиль
        style = result.get('style', {})
        style_text = style.get('narrative_style', 'Документальный')
        tone = style.get('tone', '')
        self.style_label.setText(f"{style_text}, {tone}" if tone else style_text)
        
        # Голоса
        self._populate_voices(result)
        
        # Темы
        self._populate_topics(result.get('topics', []))
        
        # Показываем шаги
        self.step2.setVisible(True)
        self.step3.setVisible(True)
        self.step4.setVisible(True)
    
    def _populate_voices(self, result: dict):
        """Заполнение списка голосов"""
        self.voice_combo.clear()
        
        # Рекомендованный голос
        rec_voice = result.get('recommended_voice')
        voice_analysis = result.get('voice_analysis', {})
        
        # Добавляем голоса по категориям
        from core.voice_library import VOICE_CATEGORIES, VOICE_LIBRARY
        
        for cat_id, cat_info in VOICE_CATEGORIES.items():
            self.voice_combo.addItem(f"--- {cat_info['name']} ---", None)
            
            for voice in VOICE_LIBRARY.values():
                if voice.name in cat_info["voices"]:
                    display = f"  {voice.name} ({voice.gender}, {voice.accent})"
                    self.voice_combo.addItem(display, voice.voice_id)
                    
                    # Выбираем рекомендованный
                    if rec_voice and voice.voice_id == rec_voice.voice_id:
                        self.voice_combo.setCurrentIndex(self.voice_combo.count() - 1)
        
        # Причина рекомендации
        if voice_analysis:
            self.voice_reason.setText(
                f"💡 Рекомендация: {voice_analysis.get('reasoning', '')}"
            )
    
    def _populate_topics(self, topics: list):
        """Заполнение списка тем"""
        self.topics_list.clear()
        for topic in topics:
            title = topic.get('title', str(topic))
            hook = topic.get('hook', '')
            viral = topic.get('viral_potential', 0)
            
            display = f"📹 {title}"
            if viral:
                display += f" ⭐{viral}/10"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, topic)
            item.setToolTip(hook)
            self.topics_list.addItem(item)
    
    def _on_subniche_changed(self, index: int):
        """При смене подниши обновляем детальную информацию"""
        sub = self.subniche_combo.currentData()
        if not sub:
            return
        
        # Основное описание
        why_works = sub.get('why_works', sub.get('description', ''))
        target = sub.get('target_audience', '')
        growth = sub.get('growth_potential', '')
        
        details = f"💡 {why_works}"
        if target:
            details += f"\n\n👥 Аудитория: {target}"
        if growth:
            details += f"\n📈 Потенциал: {growth}"
        
        # Примеры тем
        examples = sub.get('example_topics', [])
        if examples:
            details += f"\n\n📝 Примеры тем:\n• " + "\n• ".join(examples[:3])
        
        self.subniche_details.setText(details)
        
        # Метрики
        search = sub.get('search_demand', {})
        comp = sub.get('competition', {})
        viral = sub.get('viral_potential', {})
        
        search_score = search.get('score', 0) if isinstance(search, dict) else 0
        comp_score = comp.get('score', 0) if isinstance(comp, dict) else 0
        viral_score = viral.get('score', 0) if isinstance(viral, dict) else 0
        
        self.search_demand_label.setText(f"🔍 Спрос: {search_score}/10")
        self.competition_label.setText(f"⚔️ Конкуренция: {comp_score}/10")
        self.viral_label.setText(f"🚀 Вирусность: {viral_score}/10")
        
        # Цвета в зависимости от значений
        self.search_demand_label.setStyleSheet(f"color: {'#4CAF50' if search_score >= 7 else '#FF9800'}; font-weight: bold;")
        self.competition_label.setStyleSheet(f"color: {'#4CAF50' if comp_score <= 4 else '#FF9800'}; font-weight: bold;")
        self.viral_label.setStyleSheet(f"color: {'#4CAF50' if viral_score >= 7 else '#FF9800'}; font-weight: bold;")

    def generate_more_subniches(self):
        """Генерация новых подниш"""
        if not self.analysis_result:
            return
        
        self.btn_more_subniches.setEnabled(False)
        self.btn_more_subniches.setText("⏳ Генерирую...")
        
        rejected = [self.subniche_combo.itemText(i) for i in range(self.subniche_combo.count())]
        
        self.subniche_worker = SubnicheWorker(
            self.analysis_result.get('channel', {}).get('title', ''),
            rejected,
            str(self.analysis_result.get('style', {}))
        )
        self.subniche_worker.finished.connect(self._on_subniches_ready)
        self.subniche_worker.error.connect(self._on_subniche_error)
        self.subniche_worker.start()
    
    def _on_subniches_ready(self, subniches: list):
        self.btn_more_subniches.setEnabled(True)
        self.btn_more_subniches.setText("🔄 Другие подниши")
        
        self.subniche_combo.clear()
        for i, sub in enumerate(subniches):
            name = sub.get('name', str(sub))
            self.subniche_combo.addItem(name, sub)
        
        # Обновляем детали для первой подниши
        if subniches:
            self._on_subniche_changed(0)
    
    def _on_subniche_error(self, error: str):
        self.btn_more_subniches.setEnabled(True)
        self.btn_more_subniches.setText("🔄 Другие подниши")
        QMessageBox.warning(self, "Ошибка", f"Не удалось сгенерировать: {error}")
    
    def generate_more_topics(self):
        """Генерация новых тем"""
        if not self.analysis_result:
            return
        
        self.btn_more_topics.setEnabled(False)
        self.btn_more_topics.setText("⏳ Генерирую...")
        
        excluded = []
        for i in range(self.topics_list.count()):
            item = self.topics_list.item(i)
            topic_data = item.data(Qt.ItemDataRole.UserRole)
            if topic_data:
                excluded.append(topic_data.get('title', ''))
        
        import random
        self.topics_worker = TopicsWorker(
            self.subniche_combo.currentText(),
            str(self.analysis_result.get('style', {})),
            excluded,
            random.randint(1, 10000)
        )
        self.topics_worker.finished.connect(self._on_topics_ready)
        self.topics_worker.error.connect(self._on_topics_error)
        self.topics_worker.start()
    
    def _on_topics_ready(self, topics: list):
        self.btn_more_topics.setEnabled(True)
        self.btn_more_topics.setText("🔄 Другие темы")
        self._populate_topics(topics)
    
    def _on_topics_error(self, error: str):
        self.btn_more_topics.setEnabled(True)
        self.btn_more_topics.setText("🔄 Другие темы")
        QMessageBox.warning(self, "Ошибка", f"Не удалось сгенерировать: {error}")
    
    def select_all_topics(self):
        """Выбрать все темы"""
        for i in range(self.topics_list.count()):
            self.topics_list.item(i).setSelected(True)

    def start_generation_clicked(self):
        """Запуск генерации видео"""
        selected = self.topics_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну тему")
            return
        
        # Получаем voice_id
        voice_id = self.voice_combo.currentData()
        voice_name = self.voice_combo.currentText().strip().lstrip(" ")
        
        # Получаем язык контента
        lang_text = self.language_combo.currentText()
        language_map = {
            "🇷🇺 Русский": "ru",
            "🇺🇸 English": "en",
            "🇪🇸 Español": "es",
            "🇩🇪 Deutsch": "de",
            "🇫🇷 Français": "fr",
            "🇵🇹 Português": "pt",
            "🇮🇹 Italiano": "it"
        }
        language = language_map.get(lang_text, "ru")
        
        # Собираем данные для генерации
        data = {
            'subniche': self.subniche_combo.currentText(),
            'subniche_data': self.subniche_combo.currentData(),
            'voice_id': voice_id,
            'voice_name': voice_name,
            'style': self.style_label.text(),
            'duration': self.duration_combo.currentText(),
            'language': language,
            'language_display': lang_text,
            'topics': [item.data(Qt.ItemDataRole.UserRole) for item in selected],
            'channel_info': self.analysis_result.get('channel', {}),
            'thumbnail_style': self.analysis_result.get('thumbnail_style', {}),
            'save_profile': self.save_profile_check.isChecked()
        }
        
        # Сохраняем профиль если нужно
        if self.save_profile_check.isChecked():
            self._save_channel_profile(data)
        
        # Отправляем сигнал
        self.start_generation.emit(data)
        
        QMessageBox.information(
            self, "🚀 Запущено!",
            f"Добавлено {len(selected)} видео в очередь генерации.\n\n"
            f"Подниша: {data['subniche']}\n"
            f"Голос: {voice_name}\n"
            f"Язык: {lang_text}\n\n"
            "Перейдите во вкладку 'Очередь' для отслеживания.\n"
            "Вы получите уведомление в Telegram когда будет готово!"
        )
    
    def _save_channel_profile(self, data: dict):
        """Сохранение профиля канала для будущих генераций"""
        try:
            from core.channel_style import ChannelStyleManager, ChannelStyle
            
            manager = ChannelStyleManager()
            
            channel_info = data.get('channel_info', {})
            style = ChannelStyle(
                id="",  # Будет сгенерирован
                name=channel_info.get('title', 'Новый канал'),
                competitor_channel=channel_info.get('url', ''),
                main_niche=data.get('style', ''),
                sub_niche=data.get('subniche', ''),
                voice_id=data.get('voice_id', ''),
                voice_name=data.get('voice_name', ''),
                image_style=data.get('thumbnail_style', {}).get('prompt_style', ''),
                music_mood="dramatic, epic",
                transitions=["fade", "zoom"],
                text_style=data.get('thumbnail_style', {}).get('text_style', ''),
                color_scheme=data.get('thumbnail_style', {}).get('colors', '')
            )
            
            manager.save_style(style)
            print(f"[QuickStart] Профиль канала сохранён: {style.name}")
            
        except Exception as e:
            print(f"[QuickStart] Ошибка сохранения профиля: {e}")
