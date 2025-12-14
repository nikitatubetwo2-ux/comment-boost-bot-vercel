"""
Вкладка анализа конкурентов - современный интерфейс
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QListWidget, QProgressBar, QSplitter,
    QListWidgetItem, QMessageBox, QScrollArea, QFrame,
    QGridLayout, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])
from config import config, PROFILES_DIR


class ImageLoader(QThread):
    """Загрузчик изображений"""
    loaded = pyqtSignal(str, bytes)
    
    def __init__(self, url: str, item_id: str):
        super().__init__()
        self.url = url
        self.item_id = item_id
    
    def run(self):
        try:
            import urllib.request
            with urllib.request.urlopen(self.url, timeout=10) as response:
                data = response.read()
                self.loaded.emit(self.item_id, data)
        except:
            pass


class ChannelCard(QFrame):
    """Карточка канала"""
    clicked = pyqtSignal(object)
    
    def __init__(self, channel_data: dict):
        super().__init__()
        self.channel = channel_data
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            ChannelCard {
                background: #2a2a2a;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                padding: 10px;
            }
            ChannelCard:hover {
                border-color: #14a3a8;
                background: #333333;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Увеличиваем высоту если есть данные о первом видео
        has_first_video = bool(channel_data.get('_first_video_date') or channel_data.get('_days_since_first'))
        self.setMinimumHeight(115 if has_first_video else 100)
        self.setMaximumHeight(140 if has_first_video else 120)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Аватар канала
        self.avatar = QLabel()
        self.avatar.setFixedSize(70, 70)
        self.avatar.setStyleSheet("background: #444; border-radius: 35px;")
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setText("📺")
        layout.addWidget(self.avatar)
        
        # Инфо
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Название
        name = QLabel(self.channel.get('title', 'Канал')[:40])
        name.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        info_layout.addWidget(name)
        
        # Статистика в одну строку
        subs = self.channel.get('subscriber_count', 0)
        videos = self.channel.get('video_count', 0)
        views = self.channel.get('view_count', 0)
        
        stats = QLabel(f"👥 {self._format_num(subs)} • 🎬 {videos} видео • 👁 {self._format_num(views)}")
        stats.setStyleSheet("color: #aaa; font-size: 11px;")
        info_layout.addWidget(stats)
        
        # Средние просмотры и рейтинг
        avg_views = views // max(videos, 1)
        score = self._calc_score()
        
        # Проверяем есть ли данные о возрасте (для восходящих/свежих звёзд)
        star_type = self.channel.get('_star_type')
        days_since_first = self.channel.get('_days_since_first', 0)
        first_video_date = self.channel.get('_first_video_date', '')
        
        if star_type:
            # Свежие звёзды с датой первого видео
            if days_since_first > 0 or first_video_date:
                metrics = QLabel(f"{star_type}")
                metrics.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
                info_layout.addWidget(metrics)
                
                # Дополнительная строка с датой первого видео
                if first_video_date:
                    first_vid = QLabel(f"📅 Первое видео: {first_video_date} ({days_since_first}д назад)")
                    first_vid.setStyleSheet("color: #8BC34A; font-size: 10px;")
                    info_layout.addWidget(first_vid)
            else:
                engagement = self.channel.get('_engagement', 0)
                metrics = QLabel(f"{star_type} • 💎 {engagement:.0f}%")
                metrics.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
                info_layout.addWidget(metrics)
        else:
            metrics = QLabel(f"📊 ~{self._format_num(avg_views)}/видео • ⭐ {score}")
            metrics.setStyleSheet("color: #14a3a8; font-size: 11px;")
            info_layout.addWidget(metrics)
        
        layout.addLayout(info_layout, 1)
        
        # Рейтинг справа
        score_label = QLabel(f"{score}")
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_label.setFixedSize(45, 45)
        color = "#4CAF50" if score >= 70 else "#FFC107" if score >= 40 else "#f44336"
        score_label.setStyleSheet(f"""
            background: {color}; 
            border-radius: 22px; 
            font-size: 16px; 
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(score_label)
    
    def _format_num(self, n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    
    def _format_age(self, days: int) -> str:
        if days < 7:
            return f"{days} дн."
        elif days < 30:
            return f"{days // 7} нед."
        elif days < 365:
            return f"{days // 30} мес."
        else:
            return f"{days // 365} г."
    
    def _calc_score(self) -> int:
        """Расчёт рейтинга канала 0-100"""
        subs = self.channel.get('subscriber_count', 0)
        videos = self.channel.get('video_count', 0)
        views = self.channel.get('view_count', 0)
        
        if videos == 0:
            return 0
        
        avg_views = views / videos
        engagement = avg_views / max(subs, 1) * 100
        
        # Баллы за подписчиков (макс 30)
        sub_score = min(30, subs / 10000 * 10)
        
        # Баллы за engagement (макс 40)
        eng_score = min(40, engagement * 2)
        
        # Баллы за количество видео (макс 15)
        vid_score = min(15, videos / 10)
        
        # Баллы за средние просмотры (макс 15)
        view_score = min(15, avg_views / 10000 * 5)
        
        return int(sub_score + eng_score + vid_score + view_score)
    
    def set_avatar(self, data: bytes):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.avatar.setPixmap(pixmap.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.channel)


class VideoCard(QFrame):
    """Карточка видео"""
    def __init__(self, video_data: dict):
        super().__init__()
        self.video = video_data
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            VideoCard {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
            }
        """)
        self.setFixedSize(200, 175)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        
        # Превью
        self.thumb = QLabel()
        self.thumb.setFixedSize(190, 100)
        self.thumb.setStyleSheet("background: #444; border-radius: 4px;")
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setText("🎬")
        layout.addWidget(self.thumb)
        
        # Название
        title = self.video.get('title', '')[:40]
        name = QLabel(title + ('...' if len(self.video.get('title', '')) > 40 else ''))
        name.setStyleSheet("font-size: 10px; color: white;")
        name.setWordWrap(True)
        name.setMaximumHeight(28)
        layout.addWidget(name)
        
        # Статистика + дата
        views = self.video.get('view_count', 0)
        pub_date = self.video.get('published_at', '')[:10]  # YYYY-MM-DD
        date_str = self._format_date(pub_date)
        stats = QLabel(f"👁 {self._format_num(views)} • 📅 {date_str}")
        stats.setStyleSheet("color: #aaa; font-size: 9px;")
        layout.addWidget(stats)
    
    def _format_num(self, n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    
    def _format_date(self, date_str: str) -> str:
        """Форматирование даты в относительный формат"""
        if not date_str:
            return "?"
        try:
            from datetime import datetime
            pub = datetime.strptime(date_str, "%Y-%m-%d")
            now = datetime.now()
            days = (now - pub).days
            if days == 0:
                return "сегодня"
            elif days == 1:
                return "вчера"
            elif days < 7:
                return f"{days} дн."
            elif days < 30:
                return f"{days // 7} нед."
            elif days < 365:
                return f"{days // 30} мес."
            else:
                return f"{days // 365} г."
        except:
            return date_str
    
    def set_thumbnail(self, data: bytes):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.thumb.setPixmap(pixmap.scaled(190, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


class AnalyzerWorker(QThread):
    """Фоновый поток для анализа"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, task_type: str, data: dict):
        super().__init__()
        self.task_type = task_type
        self.data = data
    
    def run(self):
        try:
            if self.task_type == "search":
                self._search_channels()
            elif self.task_type == "get_videos":
                self._get_channel_videos()
            elif self.task_type == "analyze":
                self._analyze_channel()
            elif self.task_type == "analyze_niche":
                self._analyze_niche()
            elif self.task_type == "hunt_fresh":
                self._hunt_fresh_stars()
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")
    
    def _hunt_fresh_stars(self):
        """🎯 Охота за свежими звёздами"""
        from core.youtube_analyzer import YouTubeAnalyzer
        
        if not config.api.youtube_keys:
            self.error.emit("YouTube API ключ не настроен!")
            return
        
        yt = YouTubeAnalyzer(api_keys=config.api.youtube_keys)
        niche = self.data.get('niche', '')
        max_days = self.data.get('max_days', 60)
        language = self.data.get('language', 'ru')
        
        self.progress.emit(f"🎯 Охота за звёздами в нише: {niche} ({language.upper()})...")
        
        # Вызываем hunt_fresh_stars с языком
        fresh_stars = yt.hunt_fresh_stars(
            niche=niche,
            max_results=20,
            max_first_video_days=max_days,
            language=language
        )
        
        # Конвертируем в dict и добавляем метаданные
        channels_data = []
        for ch in fresh_stars:
            ch_dict = ch.to_dict() if hasattr(ch, 'to_dict') else ch
            # Копируем метаданные
            ch_dict['_star_type'] = getattr(ch, '_star_type', '')
            ch_dict['_score'] = getattr(ch, '_score', 0)
            ch_dict['_virality'] = getattr(ch, '_virality', 0)
            ch_dict['_avg_views'] = getattr(ch, '_avg_views', 0)
            ch_dict['_days_since_first'] = getattr(ch, '_days_since_first', 0)
            ch_dict['_first_video_date'] = getattr(ch, '_first_video_date', '')
            channels_data.append(ch_dict)
        
        self.progress.emit(f"✅ Найдено {len(channels_data)} свежих звёзд!")
        self.finished.emit({'type': 'fresh_stars', 'data': channels_data, 'niche': niche})
    
    def _analyze_niche(self):
        """AI анализ ниши - поиск подниш"""
        from core.groq_client import GroqClient, get_groq_client
        
        if not config.api.groq_key:
            self.error.emit("Groq API ключ не настроен!")
            return
        
        query = self.data.get('query', '')
        channels = self.data.get('channels', [])
        
        # Формируем инфо о каналах для AI
        channels_info = ""
        for i, ch in enumerate(channels[:10], 1):
            channels_info += f"{i}. {ch.get('title', '?')} - {ch.get('subscriber_count', 0):,} подписчиков, {ch.get('video_count', 0)} видео\n"
        
        self.progress.emit("🤖 AI анализ ниши...")
        groq = get_groq_client()
        
        result = groq.analyze_niche(query, channels_info)
        
        self.finished.emit({'type': 'niche_analysis', 'data': result, 'query': query})
    
    def _search_channels(self):
        from core.youtube_analyzer import YouTubeAnalyzer
        
        if not config.api.youtube_keys:
            self.error.emit("YouTube API ключ не настроен!")
            return
        
        yt = YouTubeAnalyzer(api_keys=config.api.youtube_keys)
        query = self.data.get('query', '')
        exclude_shorts = self.data.get('exclude_shorts', True)
        
        # Минимум подписчиков — низкий, чтобы найти "золотые" каналы
        min_subs = 100
        
        self.progress.emit("🔍 Поиск каналов...")
        channels = yt.search_channels(
            query, 
            max_results=20,
            min_subscribers=min_subs,
            exclude_shorts=exclude_shorts
        )
        
        # Ищем по видео — находит каналы с хорошими видео
        self.progress.emit("🎬 Поиск по популярным видео...")
        video_channels = yt.search_channels_by_videos(
            query, 
            max_results=15,
            min_subscribers=min_subs,
            exclude_shorts=exclude_shorts
        )
        
        # ГЛАВНОЕ: ищем восходящих звёзд (мало подписчиков, много просмотров)
        self.progress.emit("🚀 Поиск восходящих звёзд (золотые каналы)...")
        rising = yt.find_rising_stars(
            query,
            max_results=15,
            max_age_months=6
        )
        
        # Объединяем результаты
        channels_data = []
        seen_ids = set()
        
        for ch in channels + video_channels + rising:
            ch_dict = ch.to_dict() if hasattr(ch, 'to_dict') else ch
            if ch_dict.get('channel_id') not in seen_ids:
                seen_ids.add(ch_dict.get('channel_id'))
                channels_data.append(ch_dict)
        
        # АГРЕССИВНЫЙ фильтр Shorts каналов
        if exclude_shorts:
            self.progress.emit("🎬 Фильтрация Shorts каналов...")
            filtered = []
            for ch in channels_data:
                title = ch.get('title', '').lower()
                desc = ch.get('description', '').lower()
                videos = ch.get('video_count', 0)
                views = ch.get('view_count', 0)
                subs = ch.get('subscriber_count', 0)
                
                # Пропускаем если в названии/описании shorts
                if 'shorts' in title or 'short' in title or '#shorts' in desc:
                    continue
                
                # Пропускаем если слишком много видео для подписчиков (типичный Shorts канал)
                # Нормальный канал: ~1 видео на 1000-5000 подписчиков
                if subs > 0 and videos > subs / 500:
                    continue
                
                # Пропускаем если >50 видео но <2000 просмотров на видео
                if videos > 50:
                    avg = views / videos
                    if avg < 2000:
                        continue
                
                # Пропускаем мёртвые каналы (мало просмотров относительно подписчиков)
                if subs > 10000 and views < subs * 3:
                    continue
                
                filtered.append(ch)
            channels_data = filtered
        
        # Сортируем по качеству (engagement + подписчики)
        def quality_score(ch):
            subs = ch.get('subscriber_count', 0)
            videos = ch.get('video_count', 1)
            views = ch.get('view_count', 0)
            avg_views = views / max(videos, 1)
            engagement = avg_views / max(subs, 1) * 100
            return engagement * 0.6 + (subs / 10000) * 0.4
        
        channels_data.sort(key=quality_score, reverse=True)
        
        self.progress.emit(f"✅ Найдено {len(channels_data)} качественных каналов")
        self.finished.emit({'type': 'channels', 'data': channels_data, 'query': query})
    
    def _calc_score(self, ch: dict) -> int:
        subs = ch.get('subscriber_count', 0)
        videos = ch.get('video_count', 0)
        views = ch.get('view_count', 0)
        if videos == 0:
            return 0
        avg_views = views / videos
        engagement = avg_views / max(subs, 1) * 100
        return int(min(30, subs/10000*10) + min(40, engagement*2) + min(15, videos/10) + min(15, avg_views/10000*5))

    def _get_channel_videos(self):
        from core.youtube_analyzer import YouTubeAnalyzer
        
        if not config.api.youtube_keys:
            self.error.emit("YouTube API ключ не настроен!")
            return
        
        yt = YouTubeAnalyzer(api_keys=config.api.youtube_keys)
        channel_id = self.data.get('channel_id', '')
        
        self.progress.emit("📹 Загрузка видео канала...")
        videos = yt.get_channel_videos(channel_id, max_results=10)
        
        videos_data = [v.to_dict() for v in videos]
        self.finished.emit({'type': 'videos', 'data': videos_data, 'channel_id': channel_id})
    
    def _analyze_channel(self):
        from core.youtube_analyzer import YouTubeAnalyzer
        from core.groq_client import GroqClient, get_groq_client
        from core.channel_profile import ProfileManager
        
        if not config.api.youtube_keys:
            self.error.emit("YouTube API ключ не настроен!")
            return
        
        if not config.api.groq_key:
            self.error.emit("Groq API ключ не настроен!")
            return
        
        channel_id = self.data.get('channel_id')
        niche = self.data.get('niche', 'Общая')
        
        yt = YouTubeAnalyzer(api_keys=config.api.youtube_keys)
        groq = get_groq_client()
        
        self.progress.emit("📊 Загрузка информации...")
        channel_info = yt.get_channel_info(channel_id)
        
        if not channel_info:
            self.error.emit("Не удалось получить информацию о канале")
            return
        
        self.progress.emit("🎬 Анализ видео...")
        videos = yt.get_channel_videos(channel_id, max_results=30)
        
        self.progress.emit("📈 Расчёт статистики...")
        stats = yt.analyze_channel_stats(videos)
        
        self.progress.emit("🤖 AI анализ заголовков...")
        titles = [v.title for v in videos]
        title_analysis = groq.analyze_titles(titles)
        
        self.progress.emit("🎨 AI анализ стиля...")
        descriptions = [v.description for v in videos]
        style_analysis = groq.analyze_style(descriptions, titles)
        
        self.progress.emit("💾 Сохранение профиля...")
        pm = ProfileManager(PROFILES_DIR)
        profile = pm.create_profile_from_analysis(
            channel_info.to_dict(), stats, title_analysis, style_analysis, niche
        )
        filepath = pm.save_profile(profile)
        
        self.finished.emit({
            'type': 'analysis',
            'profile': profile,
            'stats': stats,
            'title_analysis': title_analysis,
            'style_analysis': style_analysis,
            'filepath': str(filepath)
        })


class AnalyzerTab(QWidget):
    """Вкладка анализа конкурентов"""
    profile_ready = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.current_channel = None
        self.current_profile = None
        self.worker = None
        self.image_loaders = []
        self.channel_cards = []
        self.video_cards = []
        self.all_channels = []  # Все найденные каналы
        self.fresh_stars = []   # Свежие звёзды (охота)
        self.current_tab = "all"
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        
        # === ЛЕВАЯ ПАНЕЛЬ - Поиск и каналы ===
        left = QWidget()
        left.setMaximumWidth(450)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Поиск
        search_box = QGroupBox("🔍 Поиск конкурентов")
        search_layout = QVBoxLayout(search_box)
        
        # Поле поиска
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите нишу или ключевые слова...")
        self.search_input.setStyleSheet("padding: 10px; font-size: 14px; border-radius: 8px;")
        self.search_input.returnPressed.connect(self.do_search)
        search_row.addWidget(self.search_input)
        
        self.btn_search = QPushButton("🔍")
        self.btn_search.setFixedSize(45, 40)
        self.btn_search.setStyleSheet("font-size: 18px; border-radius: 8px; background: #14a3a8;")
        self.btn_search.clicked.connect(self.do_search)
        search_row.addWidget(self.btn_search)
        search_layout.addLayout(search_row)
        
        # Фильтры
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Мин. подписчиков:"))
        self.min_subs = QComboBox()
        self.min_subs.addItems(["Любое", "1K+", "10K+", "100K+", "1M+"])
        self.min_subs.setFixedWidth(100)
        filter_row.addWidget(self.min_subs)
        
        self.exclude_shorts = QCheckBox("Исключить Shorts")
        self.exclude_shorts.setChecked(True)
        self.exclude_shorts.setToolTip("Исключить каналы с короткими видео (<60 сек)")
        filter_row.addWidget(self.exclude_shorts)
        
        filter_row.addStretch()
        search_layout.addLayout(filter_row)
        
        # Кнопка AI анализа ниши
        self.btn_analyze_niche = QPushButton("🤖 AI Анализ ниши")
        self.btn_analyze_niche.setStyleSheet("padding: 8px; background: #9c27b0; border-radius: 5px;")
        self.btn_analyze_niche.setToolTip("Найти подниши с низкой конкуренцией")
        self.btn_analyze_niche.clicked.connect(self.analyze_niche)
        self.btn_analyze_niche.setEnabled(False)
        search_layout.addWidget(self.btn_analyze_niche)
        
        left_layout.addWidget(search_box)
        
        # === ОХОТА ЗА СВЕЖИМИ ЗВЁЗДАМИ ===
        hunt_box = QGroupBox("🎯 Охота за свежими звёздами")
        hunt_box.setStyleSheet("QGroupBox { background: #1a2a1a; border: 2px solid #4CAF50; border-radius: 8px; }")
        hunt_layout = QVBoxLayout(hunt_box)
        
        # Описание
        hunt_desc = QLabel("Поиск каналов где ПЕРВОЕ видео < 60 дней, но уже бомбят!")
        hunt_desc.setStyleSheet("color: #8BC34A; font-size: 11px;")
        hunt_desc.setWordWrap(True)
        hunt_layout.addWidget(hunt_desc)
        
        # Выбор языка
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Язык:"))
        self.hunt_lang_combo = QComboBox()
        self.hunt_lang_combo.addItems([
            "🇷🇺 Русский",
            "🇺🇸 English", 
            "🇪🇸 Español",
            "🇩🇪 Deutsch",
            "🇫🇷 Français",
            "🇵🇹 Português",
            "🇮🇹 Italiano"
        ])
        self.hunt_lang_combo.currentIndexChanged.connect(self._update_niches_for_language)
        self.hunt_lang_combo.setStyleSheet("padding: 6px;")
        lang_row.addWidget(self.hunt_lang_combo, 1)
        hunt_layout.addLayout(lang_row)
        
        # Выбор ниши (будет обновляться при смене языка)
        niche_row = QHBoxLayout()
        niche_row.addWidget(QLabel("Ниша:"))
        self.niche_combo = QComboBox()
        self.niche_combo.setEditable(True)
        self._update_niches_for_language()  # Заполняем начальные ниши
        self.niche_combo.setStyleSheet("padding: 6px;")
        niche_row.addWidget(self.niche_combo, 1)
        hunt_layout.addLayout(niche_row)
        
        # Настройки
        settings_row = QHBoxLayout()
        settings_row.addWidget(QLabel("Макс. дней:"))
        self.max_days_spin = QSpinBox()
        self.max_days_spin.setRange(7, 180)
        self.max_days_spin.setValue(60)
        self.max_days_spin.setToolTip("Максимум дней с первого видео")
        settings_row.addWidget(self.max_days_spin)
        settings_row.addStretch()
        hunt_layout.addLayout(settings_row)
        
        # Кнопка охоты
        self.btn_hunt = QPushButton("🎯 ОХОТА!")
        self.btn_hunt.setStyleSheet("""
            QPushButton {
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                background: #4CAF50;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #66BB6A;
            }
        """)
        self.btn_hunt.clicked.connect(self.hunt_fresh_stars)
        hunt_layout.addWidget(self.btn_hunt)
        
        left_layout.addWidget(hunt_box)

        # Список каналов с вкладками
        channels_box = QGroupBox("📺 Результаты поиска")
        channels_box_layout = QVBoxLayout(channels_box)
        
        # Вкладки: Все / Восходящие звёзды / Свежие звёзды
        tabs_row = QHBoxLayout()
        self.tab_all = QPushButton("📺 Все")
        self.tab_all.setCheckable(True)
        self.tab_all.setChecked(True)
        self.tab_all.setStyleSheet("padding: 8px; border-radius: 5px;")
        self.tab_all.clicked.connect(lambda: self.switch_tab("all"))
        tabs_row.addWidget(self.tab_all)
        
        self.tab_rising = QPushButton("🚀 Восходящие")
        self.tab_rising.setCheckable(True)
        self.tab_rising.setStyleSheet("padding: 8px; border-radius: 5px;")
        self.tab_rising.clicked.connect(lambda: self.switch_tab("rising"))
        tabs_row.addWidget(self.tab_rising)
        
        self.tab_fresh = QPushButton("🎯 Свежие")
        self.tab_fresh.setCheckable(True)
        self.tab_fresh.setStyleSheet("padding: 8px; border-radius: 5px;")
        self.tab_fresh.clicked.connect(lambda: self.switch_tab("fresh"))
        tabs_row.addWidget(self.tab_fresh)
        channels_box_layout.addLayout(tabs_row)
        
        # Скролл для карточек
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.channels_container = QWidget()
        self.channels_layout = QVBoxLayout(self.channels_container)
        self.channels_layout.setSpacing(8)
        self.channels_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.channels_container)
        
        channels_box_layout.addWidget(scroll)
        
        # Статус
        self.status_label = QLabel("Введите запрос для поиска каналов")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        channels_box_layout.addWidget(self.status_label)
        
        left_layout.addWidget(channels_box, 1)
        
        layout.addWidget(left)
        
        # === ПРАВАЯ ПАНЕЛЬ - Детали канала ===
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Информация о канале
        info_box = QGroupBox("📊 Информация о канале")
        info_layout = QVBoxLayout(info_box)
        
        # Заголовок канала
        self.channel_header = QLabel("Выберите канал слева")
        self.channel_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #14a3a8;")
        info_layout.addWidget(self.channel_header)
        
        # Статистика в сетке
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        
        self.stat_subs = self._create_stat_widget("👥 Подписчики", "—")
        self.stat_videos = self._create_stat_widget("🎬 Видео", "—")
        self.stat_views = self._create_stat_widget("👁 Просмотры", "—")
        self.stat_avg = self._create_stat_widget("📊 Среднее/видео", "—")
        self.stat_engagement = self._create_stat_widget("💎 Engagement", "—")
        self.stat_score = self._create_stat_widget("⭐ Рейтинг", "—")
        
        stats_grid.addWidget(self.stat_subs, 0, 0)
        stats_grid.addWidget(self.stat_videos, 0, 1)
        stats_grid.addWidget(self.stat_views, 0, 2)
        stats_grid.addWidget(self.stat_avg, 1, 0)
        stats_grid.addWidget(self.stat_engagement, 1, 1)
        stats_grid.addWidget(self.stat_score, 1, 2)
        
        info_layout.addLayout(stats_grid)
        right_layout.addWidget(info_box)
        
        # Последние видео
        videos_box = QGroupBox("🎬 Последние видео канала")
        videos_box.setStyleSheet("QGroupBox { background: #1e1e1e; border-radius: 8px; }")
        videos_inner = QVBoxLayout(videos_box)
        
        # Статус загрузки видео
        self.videos_status = QLabel("Выберите канал для просмотра видео")
        self.videos_status.setStyleSheet("color: #888; font-size: 11px;")
        videos_inner.addWidget(self.videos_status)
        
        videos_scroll = QScrollArea()
        videos_scroll.setWidgetResizable(True)
        videos_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        videos_scroll.setMinimumHeight(190)
        videos_scroll.setMaximumHeight(200)
        videos_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.videos_container = QWidget()
        self.videos_layout = QHBoxLayout(self.videos_container)
        self.videos_layout.setSpacing(10)
        self.videos_layout.setContentsMargins(5, 5, 5, 5)
        self.videos_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        videos_scroll.setWidget(self.videos_container)
        
        videos_inner.addWidget(videos_scroll)
        right_layout.addWidget(videos_box)
        
        # Результаты анализа
        analysis_box = QGroupBox("🤖 AI Анализ")
        analysis_layout = QVBoxLayout(analysis_box)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlaceholderText("Нажмите 'Анализировать' для AI-анализа канала...")
        self.analysis_text.setMaximumHeight(150)
        analysis_layout.addWidget(self.analysis_text)
        
        right_layout.addWidget(analysis_box)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.btn_analyze = QPushButton("🔬 Анализировать канал")
        self.btn_analyze.setStyleSheet("padding: 12px; font-size: 14px; background: #e63946; border-radius: 8px;")
        self.btn_analyze.clicked.connect(self.analyze_channel)
        self.btn_analyze.setEnabled(False)
        btn_layout.addWidget(self.btn_analyze)
        
        self.btn_use = QPushButton("✅ Использовать для генерации")
        self.btn_use.setStyleSheet("padding: 12px; font-size: 14px; background: #14a3a8; border-radius: 8px;")
        self.btn_use.clicked.connect(self.use_profile)
        self.btn_use.setEnabled(False)
        btn_layout.addWidget(self.btn_use)
        
        right_layout.addLayout(btn_layout)
        
        # Прогресс
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setStyleSheet("QProgressBar { height: 20px; border-radius: 10px; }")
        right_layout.addWidget(self.progress)
        
        layout.addWidget(right, 1)

    def _create_stat_widget(self, label: str, value: str) -> QFrame:
        """Создание виджета статистики"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(lbl)
        
        val = QLabel(value)
        val.setObjectName("value")
        val.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(val)
        
        return frame
    
    def _update_stat(self, widget: QFrame, value: str):
        """Обновление значения статистики"""
        val_label = widget.findChild(QLabel, "value")
        if val_label:
            val_label.setText(value)
    
    def _format_num(self, n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    
    def do_search(self):
        """Выполнить поиск"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Ошибка", "Введите поисковый запрос")
            return
        
        self.clear_channels()
        self.status_label.setText("🔍 Поиск...")
        self.progress.setVisible(True)
        self.btn_analyze_niche.setEnabled(False)
        self.last_query = query
        
        self.worker = AnalyzerWorker("search", {
            'query': query,
            'exclude_shorts': self.exclude_shorts.isChecked()
        })
        self.worker.progress.connect(lambda m: self.status_label.setText(m))
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def _update_niches_for_language(self):
        """Обновление списка ниш при смене языка"""
        # Словарь ниш по языкам
        niches_by_lang = {
            "🇷🇺 Русский": [
                "военная история",
                "вторая мировая война",
                "история России",
                "криминал",
                "загадки истории",
                "тайны СССР",
                "биографии",
                "исторические личности",
                "древний мир",
                "средневековье",
                "холодная война",
                "мистика и загадки"
            ],
            "🇺🇸 English": [
                "world war 2 history",
                "military history",
                "true crime",
                "historical mysteries",
                "biography documentary",
                "ancient history",
                "cold war secrets",
                "medieval history",
                "war stories",
                "historical figures",
                "unsolved mysteries",
                "crime documentary"
            ],
            "🇪🇸 Español": [
                "historia militar",
                "segunda guerra mundial",
                "crímenes reales",
                "misterios históricos",
                "biografías",
                "historia antigua",
                "guerra fría",
                "historia medieval",
                "documentales de crimen"
            ],
            "🇩🇪 Deutsch": [
                "Militärgeschichte",
                "Zweiter Weltkrieg",
                "True Crime",
                "historische Mysterien",
                "Biografien",
                "Antike Geschichte",
                "Kalter Krieg",
                "Mittelalter"
            ],
            "🇫🇷 Français": [
                "histoire militaire",
                "seconde guerre mondiale",
                "crimes réels",
                "mystères historiques",
                "biographies",
                "histoire ancienne",
                "guerre froide"
            ],
            "🇵🇹 Português": [
                "história militar",
                "segunda guerra mundial",
                "crimes reais",
                "mistérios históricos",
                "biografias",
                "história antiga"
            ],
            "🇮🇹 Italiano": [
                "storia militare",
                "seconda guerra mondiale",
                "crimini veri",
                "misteri storici",
                "biografie",
                "storia antica"
            ]
        }
        
        lang = self.hunt_lang_combo.currentText()
        niches = niches_by_lang.get(lang, niches_by_lang["🇷🇺 Русский"])
        
        self.niche_combo.clear()
        self.niche_combo.addItems(niches)
    
    def hunt_fresh_stars(self):
        """🎯 Охота за свежими звёздами"""
        niche = self.niche_combo.currentText().strip()
        if not niche:
            QMessageBox.warning(self, "Ошибка", "Выберите или введите нишу")
            return
        
        # Получаем код языка для фильтрации
        lang_text = self.hunt_lang_combo.currentText()
        lang_codes = {
            "🇷🇺 Русский": "ru",
            "🇺🇸 English": "en",
            "🇪🇸 Español": "es",
            "🇩🇪 Deutsch": "de",
            "🇫🇷 Français": "fr",
            "🇵🇹 Português": "pt",
            "🇮🇹 Italiano": "it"
        }
        lang_code = lang_codes.get(lang_text, "ru")
        
        self.clear_channels()
        self.fresh_stars = []  # Отдельный список для свежих звёзд
        self.status_label.setText(f"🎯 Охота в нише: {niche} ({lang_code.upper()})...")
        self.progress.setVisible(True)
        
        max_days = self.max_days_spin.value()
        
        self.worker = AnalyzerWorker("hunt_fresh", {
            'niche': niche,
            'max_days': max_days,
            'language': lang_code
        })
        self.worker.progress.connect(lambda m: self.status_label.setText(m))
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def analyze_niche(self):
        """AI анализ ниши"""
        if not self.all_channels:
            QMessageBox.warning(self, "Ошибка", "Сначала выполните поиск")
            return
        
        self.progress.setVisible(True)
        self.status_label.setText("🤖 AI анализ ниши...")
        
        self.worker = AnalyzerWorker("analyze_niche", {
            'query': getattr(self, 'last_query', ''),
            'channels': self.all_channels
        })
        self.worker.progress.connect(lambda m: self.status_label.setText(m))
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def clear_channels(self):
        """Очистка списка каналов"""
        for card in self.channel_cards:
            card.deleteLater()
        self.channel_cards.clear()
    
    def clear_videos(self):
        """Очистка списка видео"""
        for card in self.video_cards:
            card.deleteLater()
        self.video_cards.clear()
    
    def switch_tab(self, tab: str):
        """Переключение вкладок"""
        self.current_tab = tab
        self.tab_all.setChecked(tab == "all")
        self.tab_rising.setChecked(tab == "rising")
        self.tab_fresh.setChecked(tab == "fresh")
        
        # Обновляем стили
        active_style = "padding: 8px; border-radius: 5px; background: #14a3a8;"
        inactive_style = "padding: 8px; border-radius: 5px; background: #3d3d3d;"
        fresh_active = "padding: 8px; border-radius: 5px; background: #4CAF50;"
        
        self.tab_all.setStyleSheet(active_style if tab == "all" else inactive_style)
        self.tab_rising.setStyleSheet(active_style if tab == "rising" else inactive_style)
        self.tab_fresh.setStyleSheet(fresh_active if tab == "fresh" else inactive_style)
        
        # Перерисовываем каналы
        self.display_channels()
    
    def on_error(self, message: str):
        self.progress.setVisible(False)
        self.status_label.setText("❌ Ошибка")
        QMessageBox.critical(self, "Ошибка", message)
    
    def on_finished(self, result: dict):
        self.progress.setVisible(False)
        result_type = result.get('type')
        
        if result_type == 'channels':
            self.all_channels = result['data']
            self.btn_analyze_niche.setEnabled(True)
            self.display_channels()
        
        elif result_type == 'fresh_stars':
            self.fresh_stars = result['data']
            self.current_tab = "fresh"
            self.switch_tab("fresh")
            QMessageBox.information(
                self, "🎯 Охота завершена!", 
                f"Найдено {len(self.fresh_stars)} свежих звёзд в нише '{result.get('niche', '')}'!\n\n"
                "Это каналы где первое видео < 60 дней, но уже хорошие показатели."
            )
        
        elif result_type == 'niche_analysis':
            self._show_niche_analysis(result['data'])
        
        elif result_type == 'videos':
            self.clear_videos()
            videos = result['data']
            
            if not videos:
                self.videos_status.setText("❌ Видео не найдены")
                return
            
            # Показываем статистику видео
            total_views = sum(v.get('view_count', 0) for v in videos)
            avg_views = total_views // len(videos) if videos else 0
            self.videos_status.setText(f"📹 {len(videos)} видео • Среднее: {self._format_num(avg_views)} просмотров")
            
            for vid in videos[:6]:
                card = VideoCard(vid)
                self.videos_layout.addWidget(card)
                self.video_cards.append(card)
                
                # Загрузка превью
                if vid.get('thumbnail_url'):
                    loader = ImageLoader(vid['thumbnail_url'], vid['video_id'])
                    loader.loaded.connect(lambda vid_id, data: self._set_video_thumb(vid_id, data))
                    self.image_loaders.append(loader)
                    loader.start()
        
        elif result_type == 'analysis':
            profile = result['profile']
            stats = result['stats']
            title_analysis = result.get('title_analysis', {})
            style_analysis = result.get('style_analysis', {})
            
            self.current_profile = profile
            
            # Отображаем анализ
            text = f"""🎯 СТИЛЬ: {style_analysis.get('narrative_style', '?')}
📢 ТОН: {style_analysis.get('tone', '?')}
👥 АУДИТОРИЯ: {style_analysis.get('target_audience', '?')}

📊 ТРИГГЕРЫ ЗАГОЛОВКОВ:
"""
            triggers = title_analysis.get('triggers', {})
            for cat, items in triggers.items():
                if items:
                    text += f"• {cat}: {', '.join(items[:3])}\n"
            
            voice = style_analysis.get('recommended_voice', {})
            if voice:
                text += f"\n🎙 ГОЛОС: {voice.get('gender', '?')}, {voice.get('type', '?')}, {voice.get('pace', '?')}"
            
            self.analysis_text.setText(text)
            self.btn_use.setEnabled(True)
            
            QMessageBox.information(self, "✅ Готово", f"Профиль '{profile.name}' создан!")

    def display_channels(self):
        """Отображение каналов в зависимости от вкладки"""
        self.clear_channels()
        
        # Выбираем источник данных
        if self.current_tab == "fresh" and hasattr(self, 'fresh_stars') and self.fresh_stars:
            channels = self.fresh_stars.copy()
            self.status_label.setText(f"🎯 Свежие звёзды: {len(channels)}")
        else:
            channels = self.all_channels.copy()
            
            # Фильтрация по подписчикам
            min_subs_filter = self.min_subs.currentText()
            if min_subs_filter != "Любое":
                min_val = {"1K+": 1000, "10K+": 10000, "100K+": 100000, "1M+": 1000000}.get(min_subs_filter, 0)
                channels = [c for c in channels if c.get('subscriber_count', 0) >= min_val]
            
            if self.current_tab == "rising":
                # Восходящие звёзды - молодые каналы с хорошими показателями
                channels = self._filter_rising_stars(channels)
                self.status_label.setText(f"🚀 Восходящие звёзды: {len(channels)}")
            else:
                self.status_label.setText(f"✅ Найдено: {len(channels)} каналов")
        
        for ch in channels:
            card = ChannelCard(ch)
            card.clicked.connect(self.on_channel_clicked)
            self.channels_layout.addWidget(card)
            self.channel_cards.append(card)
            
            # Загрузка аватара
            if ch.get('thumbnail_url'):
                loader = ImageLoader(ch['thumbnail_url'], ch['channel_id'])
                loader.loaded.connect(lambda cid, data: self._set_channel_avatar(cid, data))
                self.image_loaders.append(loader)
                loader.start()
    
    def _filter_rising_stars(self, channels: list) -> list:
        """Фильтр восходящих звёзд - приоритет самым молодым каналам"""
        from datetime import datetime
        
        very_young = []  # < 3 месяцев
        young = []       # 3-6 месяцев
        growing = []     # 6-12 месяцев
        established = [] # > 1 года но с хорошими показателями
        
        for ch in channels:
            pub_date = ch.get('published_at', '')
            
            subs = ch.get('subscriber_count', 0)
            videos = ch.get('video_count', 0)
            views = ch.get('view_count', 0)
            
            if videos == 0:
                continue
            
            avg_views = views / videos
            
            # Определяем возраст канала
            age_days = 9999
            if pub_date:
                try:
                    for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                        try:
                            pub_clean = pub_date[:19].replace('Z', '')
                            created = datetime.strptime(pub_clean, fmt[:len(pub_clean)])
                            age_days = max((datetime.now() - created).days, 1)
                            break
                        except:
                            continue
                except:
                    pass
            
            # Метрики
            engagement = avg_views / max(subs, 1) * 100 if subs > 0 else 0
            growth_rate = views / max(age_days, 1)
            
            ch['_age_days'] = age_days
            ch['_engagement'] = engagement
            ch['_avg_views'] = avg_views
            ch['_growth_rate'] = growth_rate
            
            # Проверка активности: минимум 1 видео в 2 месяца
            # Если канал старше 60 дней, должно быть минимум age_days/60 видео
            min_expected_videos = max(1, age_days // 60)
            is_active = videos >= min_expected_videos * 0.5  # Допускаем 50% от ожидаемого
            
            if not is_active:
                continue  # Пропускаем неактивные каналы
            
            # Категоризация по возрасту
            if age_days <= 90:  # < 3 месяцев
                ch['_star_type'] = f'🔥 {age_days}д - НОВИЧОК'
                ch['_priority'] = 1
                very_young.append(ch)
            elif age_days <= 180:  # 3-6 месяцев
                ch['_star_type'] = f'⭐ {age_days // 30}мес'
                ch['_priority'] = 2
                young.append(ch)
            elif age_days <= 365:  # 6-12 месяцев
                ch['_star_type'] = f'📈 {age_days // 30}мес'
                ch['_priority'] = 3
                growing.append(ch)
            elif engagement >= 30 or avg_views >= 10000:  # Старше но успешные
                ch['_star_type'] = f'💎 {engagement:.0f}% eng'
                ch['_priority'] = 4
                established.append(ch)
        
        # Сортируем каждую группу по engagement
        for group in [very_young, young, growing, established]:
            group.sort(key=lambda x: x.get('_engagement', 0), reverse=True)
        
        # Объединяем: сначала самые молодые
        return very_young + young + growing + established
    
    def _format_age_short(self, days: int) -> str:
        """Короткий формат возраста"""
        if days <= 30:
            return f"{days}д"
        elif days <= 365:
            return f"{days // 30}мес"
        else:
            return f"{days // 365}г"
    
    def _set_channel_avatar(self, channel_id: str, data: bytes):
        """Установка аватара канала"""
        for card in self.channel_cards:
            if card.channel.get('channel_id') == channel_id:
                card.set_avatar(data)
                break
    
    def _set_video_thumb(self, video_id: str, data: bytes):
        """Установка превью видео"""
        for card in self.video_cards:
            if card.video.get('video_id') == video_id:
                card.set_thumbnail(data)
                break
    
    def on_channel_clicked(self, channel: dict):
        """Обработка клика на канал"""
        self.current_channel = channel
        
        # Обновляем заголовок
        self.channel_header.setText(f"📺 {channel.get('title', 'Канал')}")
        
        # Обновляем статистику
        subs = channel.get('subscriber_count', 0)
        videos = channel.get('video_count', 0)
        views = channel.get('view_count', 0)
        avg_views = views // max(videos, 1)
        engagement = round(avg_views / max(subs, 1) * 100, 1)
        
        # Расчёт рейтинга
        sub_score = min(30, subs / 10000 * 10)
        eng_score = min(40, engagement * 2)
        vid_score = min(15, videos / 10)
        view_score = min(15, avg_views / 10000 * 5)
        score = int(sub_score + eng_score + vid_score + view_score)
        
        self._update_stat(self.stat_subs, self._format_num(subs))
        self._update_stat(self.stat_videos, str(videos))
        self._update_stat(self.stat_views, self._format_num(views))
        self._update_stat(self.stat_avg, self._format_num(avg_views))
        self._update_stat(self.stat_engagement, f"{engagement}%")
        self._update_stat(self.stat_score, f"{score}/100")
        
        self.btn_analyze.setEnabled(True)
        
        # Загружаем видео канала
        self.clear_videos()
        self.videos_status.setText("⏳ Загрузка видео...")
        self.worker = AnalyzerWorker("get_videos", {'channel_id': channel.get('channel_id')})
        self.worker.progress.connect(lambda m: self.status_label.setText(m))
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def analyze_channel(self):
        """Полный AI анализ канала"""
        if not self.current_channel:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите канал")
            return
        
        self.progress.setVisible(True)
        self.status_label.setText("🤖 AI анализ...")
        
        self.worker = AnalyzerWorker("analyze", {
            'channel_id': self.current_channel.get('channel_id'),
            'niche': self.search_input.text().strip() or "Общая"
        })
        self.worker.progress.connect(lambda m: self.status_label.setText(m))
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def use_profile(self):
        """Использовать профиль для генерации"""
        if self.current_profile:
            self.profile_ready.emit(self.current_profile)
            QMessageBox.information(self, "✅ Готово", "Профиль передан. Перейдите на вкладку 'Сценарий'.")
    
    def _show_niche_analysis(self, data: dict):
        """Отображение AI анализа ниши"""
        if 'raw_analysis' in data:
            self.analysis_text.setText(data['raw_analysis'])
            return
        
        niche = data.get('niche_analysis', {})
        subniches = data.get('subniches', [])
        
        text = f"""🎯 АНАЛИЗ НИШИ

📊 НАСЫЩЕННОСТЬ: {niche.get('saturation', '?')} ({niche.get('saturation_score', '?')}/100)
🏆 КОНКУРЕНТОВ: {niche.get('main_competitors', '?')}
💎 ПОТЕНЦИАЛ: {niche.get('opportunity_score', '?')}/100

📝 {niche.get('summary', '')}

{'='*40}
🚀 ПОДНИШИ С НИЗКОЙ КОНКУРЕНЦИЕЙ:
{'='*40}
"""
        
        for i, sub in enumerate(subniches, 1):
            text += f"""
{i}. {sub.get('name', '?')}
   📈 Конкуренция: {sub.get('competition', '?')}
   💎 Потенциал: {sub.get('potential', '?')}
   🎯 Почему работает: {sub.get('why_works', '')}
   🔥 Уникальный угол: {sub.get('unique_angle', '')}
   👥 Аудитория: {sub.get('target_audience', '')}
   📹 Примеры тем: {', '.join(sub.get('example_topics', []))}
"""
        
        text += f"""
{'='*40}
💡 РЕКОМЕНДАЦИЯ:
{data.get('recommendation', '')}

📋 СТРАТЕГИЯ:
{data.get('strategy', '')}
"""
        
        self.analysis_text.setText(text)
        QMessageBox.information(self, "🤖 AI Анализ", "Анализ ниши завершён! Смотрите результаты справа.")
