"""
Главное окно приложения Video Factory
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QMenuBar, QMenu, QToolBar,
    QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from ui.tabs.quickstart_tab import QuickStartTab
from ui.tabs.analyzer_tab import AnalyzerTab
from ui.tabs.script_tab import ScriptTab
from ui.tabs.media_tab import MediaTab
from ui.tabs.editor_tab import EditorTab
from ui.tabs.seo_tab import SEOTab
from ui.tabs.queue_tab import QueueTab
from ui.tabs.profiles_tab import ProfilesTab
from ui.tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Factory - YouTube Content Automation")
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
        self.init_menu()
        self.init_statusbar()
        self.connect_signals()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        header = QLabel("🎬 Video Factory")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #14a3a8;
            padding: 10px;
        """)
        layout.addWidget(header)
        
        # Табы
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Добавляем вкладки
        self.quickstart_tab = QuickStartTab()
        self.analyzer_tab = AnalyzerTab()
        self.script_tab = ScriptTab()
        self.media_tab = MediaTab()
        self.editor_tab = EditorTab()
        self.seo_tab = SEOTab()
        self.queue_tab = QueueTab()
        self.profiles_tab = ProfilesTab()
        self.settings_tab = SettingsTab()
        
        self.tabs.addTab(self.quickstart_tab, "🚀 Быстрый старт")
        self.tabs.addTab(self.analyzer_tab, "🔍 Анализ")
        self.tabs.addTab(self.script_tab, "📝 Сценарий")
        self.tabs.addTab(self.media_tab, "🖼 Медиа")
        self.tabs.addTab(self.editor_tab, "🎬 Монтаж")
        self.tabs.addTab(self.seo_tab, "📈 SEO")
        self.tabs.addTab(self.queue_tab, "📋 Очередь")
        self.tabs.addTab(self.profiles_tab, "📺 Профили")
        self.tabs.addTab(self.settings_tab, "⚙️ Настройки")
        
        layout.addWidget(self.tabs)
    
    def connect_signals(self):
        """Связывание сигналов между вкладками"""
        # Быстрый старт -> Очередь
        self.quickstart_tab.start_generation.connect(self.on_quickstart_generation)
        
        # Анализ -> Сценарий
        self.analyzer_tab.profile_ready.connect(self.on_profile_ready)
        
        # Сценарий -> Медиа
        self.script_tab.script_ready.connect(self.on_script_ready)
        
        # Медиа -> Монтаж
        self.media_tab.media_ready.connect(self.on_media_ready)
    
    def on_quickstart_generation(self, data: dict):
        """Обработка запуска генерации из Быстрого старта"""
        # Передаём данные в очередь
        self.queue_tab.add_batch_from_quickstart(data)
        # Переключаемся на вкладку очереди
        self.tabs.setCurrentWidget(self.queue_tab)
        self.statusbar.showMessage(f"Добавлено {len(data.get('topics', []))} видео в очередь")
    
    def on_profile_ready(self, profile):
        """Профиль готов — передаём в сценарий"""
        self.script_tab.set_profile(profile)
        self.statusbar.showMessage(f"Профиль '{profile.name}' загружен")
    
    def on_script_ready(self, data):
        """Сценарий готов — передаём в медиа"""
        self.media_tab.set_script_data(data)
        self.statusbar.showMessage("Сценарий передан в раздел Медиа")
    
    def on_media_ready(self, data):
        """Медиа готово — передаём в монтаж"""
        self.editor_tab.set_media_data(data)
        self.statusbar.showMessage("Медиа передано в раздел Монтаж")
    
    def init_menu(self):
        """Инициализация меню"""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu("Файл")
        
        new_project = QAction("Новый проект", self)
        new_project.setShortcut("Ctrl+N")
        new_project.triggered.connect(self.new_project)
        file_menu.addAction(new_project)
        
        open_project = QAction("Открыть проект", self)
        open_project.setShortcut("Ctrl+O")
        file_menu.addAction(open_project)
        
        save_project = QAction("Сохранить проект", self)
        save_project.setShortcut("Ctrl+S")
        file_menu.addAction(save_project)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Переход
        nav_menu = menubar.addMenu("Переход")
        
        tabs_actions = [
            ("Быстрый старт", "Ctrl+1", 0),
            ("Анализ", "Ctrl+2", 1),
            ("Сценарий", "Ctrl+3", 2),
            ("Медиа", "Ctrl+4", 3),
            ("Монтаж", "Ctrl+5", 4),
            ("SEO", "Ctrl+6", 5),
            ("Очередь", "Ctrl+7", 6),
            ("Профили", "Ctrl+8", 7),
            ("Настройки", "Ctrl+9", 8),
        ]
        
        for name, shortcut, index in tabs_actions:
            action = QAction(name, self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, i=index: self.tabs.setCurrentIndex(i))
            nav_menu.addAction(action)
        
        # Помощь
        help_menu = menubar.addMenu("Помощь")
        
        about = QAction("О программе", self)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)
    
    def init_statusbar(self):
        """Инициализация статусбара"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готов к работе. Начните с настройки API ключей (⚙️ Настройки)")
    
    def new_project(self):
        """Создание нового проекта"""
        reply = QMessageBox.question(
            self, "Новый проект",
            "Создать новый проект? Несохранённые данные будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.statusbar.showMessage("Создан новый проект")
    
    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(
            self, "О программе",
            """<h2>Video Factory v1.0.0</h2>
            <p>Автоматизация создания YouTube контента</p>
            <p><b>Возможности:</b></p>
            <ul>
                <li>Анализ конкурентов (YouTube API)</li>
                <li>AI генерация сценариев (Groq)</li>
                <li>Генерация изображений (Pollinations.ai)</li>
                <li>Озвучка (ElevenLabs)</li>
                <li>Автоматический монтаж (MoviePy)</li>
                <li>SEO оптимизация</li>
            </ul>
            <p><b>Горячие клавиши:</b></p>
            <ul>
                <li>Ctrl+1-6 — переключение вкладок</li>
                <li>Ctrl+S — сохранить проект</li>
                <li>Ctrl+Q — выход</li>
            </ul>
            """
        )
