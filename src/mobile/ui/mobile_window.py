
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import urllib.request

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QComboBox, QSpinBox,
    QProgressBar, QButtonGroup, QListWidget, QListWidgetItem, 
    QFrame, QMessageBox, QStackedWidget, QScrollArea, QSizePolicy,
    QScroller, QGraphicsDropShadowEffect, QDialog, QGridLayout,
    QInputDialog, QFileDialog, QLineEdit
)
from PySide6.QtCore import Qt, Slot, QSize, QRect, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QThread, Signal, QByteArray
from PySide6.QtGui import (
    QPalette, QColor, QFont, QIcon, QPainter, QLinearGradient, 
    QBrush, QPen, QRadialGradient, QFontDatabase, QClipboard, QGuiApplication,
    QPixmap, QImage
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from src.core.worker import DownloadManager, DownloadMode
from src.core.utils import extract_youtube_urls, resource_path

# --- CONSTANTS ---
COLOR_BG = "#0A0A0A"
COLOR_SURFACE = "#161616"
COLOR_SURFACE_2 = "#1C1C1E"
COLOR_ACCENT = "#FF3131"
COLOR_ACCENT_DARK = "#CC2020"
COLOR_TEXT_HEAD = "#FFFFFF"
COLOR_TEXT_BODY = "#8E8E93"
COLOR_BORDER = "#2C2C2E"
COLOR_SUCCESS = "#30D158"
COLOR_ERROR = "#FF453A"

# --- STYLESHEET ---
GLOBAL_STYLES = f"""
    QMainWindow, QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT_HEAD};
        font-family: Arial, Helvetica, sans-serif;
        font-size: 14px;
    }}
    QTextEdit, QLineEdit {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 12px;
        padding: 14px;
        color: {COLOR_TEXT_HEAD};
        font-size: 15px;
        selection-background-color: {COLOR_ACCENT};
    }}
    QTextEdit:focus, QLineEdit:focus {{
        border-color: {COLOR_ACCENT};
    }}
    QComboBox, QSpinBox {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        padding: 12px;
        color: {COLOR_TEXT_HEAD};
        min-height: 35px;
    }}
    QComboBox:focus, QSpinBox:focus {{
        border-color: {COLOR_ACCENT};
    }}
    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QListWidget {{
        background: transparent;
        border: none;
        outline: none;
    }}
    QListWidget::item {{
        background-color: {COLOR_SURFACE};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        color: {COLOR_TEXT_HEAD};
    }}
    QListWidget::item:selected {{
        background-color: {COLOR_SURFACE_2};
        border: 1px solid {COLOR_ACCENT};
    }}
"""

# --- CUSTOM WIDGETS ---

class NeonButton(QPushButton):
    """Primary Action Button with Glow"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(56)
        self.setFont(QFont("Arial", 16, QFont.Bold))
        self.setCursor(Qt.PointingHandCursor)
        self._update_style(False)
        
        # Glow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(255, 49, 49, 150))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _update_style(self, loading=False):
        bg = "#555" if loading else COLOR_ACCENT
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border-radius: 14px;
                border: none;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background-color: {'#666' if loading else '#E02828'}; }}
            QPushButton:pressed {{ background-color: {'#444' if loading else '#CC2020'}; }}
        """)
    
    def set_loading(self, loading=True):
        self._update_style(loading)
        self.setEnabled(not loading)

class SecondaryButton(QPushButton):
    """Secondary Action Button"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_HEAD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ 
                background-color: {COLOR_SURFACE_2}; 
                border-color: {COLOR_ACCENT}; 
            }}
            QPushButton:pressed {{ background-color: #333; }}
        """)

class NavButton(QPushButton):
    """Bottom Navigation Button"""
    def __init__(self, icon_text, label, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.label = label
        self.setCheckable(True)
        self.setFixedSize(80, 60)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
    
    def _update_style(self):
        color = COLOR_ACCENT if self.isChecked() else COLOR_TEXT_BODY
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {color};
            }}
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        color = QColor(COLOR_ACCENT) if self.isChecked() else QColor(COLOR_TEXT_BODY)
        painter.setPen(color)
        
        # Icon
        icon_font = QFont("Arial", 22)
        painter.setFont(icon_font)
        painter.drawText(QRect(0, 5, self.width(), 30), Qt.AlignCenter, self.icon_text)
        
        # Label
        label_font = QFont("Arial", 10, QFont.Bold if self.isChecked() else QFont.Normal)
        painter.setFont(label_font)
        painter.drawText(QRect(0, 38, self.width(), 20), Qt.AlignCenter, self.label)

class BentoCard(QFrame):
    """Card Container with Glassmorphism"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 20px;
            }}
        """)

class ThumbnailLoader(QThread):
    """Background thread to load thumbnails"""
    thumbnail_loaded = Signal(str, QPixmap)  # item_id, pixmap
    
    def __init__(self, item_id, url):
        super().__init__()
        self.item_id = item_id
        self.url = url
    
    def run(self):
        try:
            # Download image
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
            
            # Convert to QPixmap
            image = QImage()
            image.loadFromData(QByteArray(data))
            
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                # Scale to 60x60 with aspect ratio
                pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                # Crop to center
                if pixmap.width() > 60 or pixmap.height() > 60:
                    x = (pixmap.width() - 60) // 2
                    y = (pixmap.height() - 60) // 2
                    pixmap = pixmap.copy(x, y, 60, 60)
                
                self.thumbnail_loaded.emit(self.item_id, pixmap)
        except Exception as e:
            print(f"Thumbnail load error: {e}")

class ActivityRow(QWidget):
    """Download Item Row with Thumbnail and Live Progress"""
    def __init__(self, item_id, title, status="Preparing...", thumbnail_url="", parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.thumbnail_loader = None
        self.setFixedHeight(85)
        self.setStyleSheet(f"background-color: {COLOR_SURFACE}; border-radius: 14px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 14, 10)
        layout.setSpacing(12)
        
        # Thumbnail Container
        self.thumb_container = QWidget()
        self.thumb_container.setFixedSize(65, 65)
        self.thumb_container.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a1a, stop:1 #2a2a2a);
            border-radius: 10px;
        """)
        
        thumb_layout = QVBoxLayout(self.thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setAlignment(Qt.AlignCenter)
        
        # Thumbnail Label (will show image or icon)
        self.thumb_label = QLabel("⏳")
        self.thumb_label.setFixedSize(60, 60)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet(f"""
            background: transparent;
            border-radius: 8px; 
            color: {COLOR_ACCENT}; 
            font-size: 24px;
        """)
        thumb_layout.addWidget(self.thumb_label)
        layout.addWidget(self.thumb_container)
        
        # Load thumbnail if URL provided
        if thumbnail_url:
            self._load_thumbnail(thumbnail_url)
        
        # Info Section
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        vbox.setContentsMargins(0, 2, 0, 2)
        
        display_title = title[:38] + "..." if len(title) > 38 else title
        self.title_lbl = QLabel(display_title)
        self.title_lbl.setStyleSheet(f"color: {COLOR_TEXT_HEAD}; font-weight: 600; font-size: 13px; background: transparent;")
        
        self.status_lbl = QLabel(status)
        self.status_lbl.setStyleSheet(f"color: {COLOR_TEXT_BODY}; font-size: 11px; background: transparent;")
        
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(4)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet(f"""
            QProgressBar {{ 
                border: none; 
                background: #2a2a2a; 
                border-radius: 2px; 
            }}
            QProgressBar::chunk {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_ACCENT}, stop:1 #FF6666);
                border-radius: 2px; 
            }}
        """)
        
        vbox.addWidget(self.title_lbl)
        vbox.addWidget(self.status_lbl)
        vbox.addWidget(self.pbar)
        
        layout.addLayout(vbox, 1)
    
    def _load_thumbnail(self, url):
        """Load thumbnail in background thread"""
        self.thumbnail_loader = ThumbnailLoader(self.item_id, url)
        self.thumbnail_loader.thumbnail_loaded.connect(self._on_thumbnail_loaded)
        self.thumbnail_loader.start()
    
    @Slot(str, QPixmap)
    def _on_thumbnail_loaded(self, item_id, pixmap):
        """Called when thumbnail is loaded"""
        if item_id == self.item_id and not pixmap.isNull():
            # Create rounded pixmap
            rounded = QPixmap(60, 60)
            rounded.fill(Qt.transparent)
            
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(pixmap))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(0, 0, 60, 60, 8, 8)
            painter.end()
            
            self.thumb_label.setPixmap(rounded)
            self.thumb_label.setStyleSheet("background: transparent; border-radius: 8px;")

    def set_thumbnail(self, thumbnail_url):
        """Set thumbnail from URL"""
        if thumbnail_url:
            self._load_thumbnail(thumbnail_url)

    def update_progress(self, progress, status):
        self.pbar.setValue(int(progress))
        self.status_lbl.setText(status)
        
        # Only show download icon if no thumbnail loaded yet
        if "downloading" in status.lower() or progress > 0:
            if self.thumb_label.pixmap() is None or self.thumb_label.pixmap().isNull():
                self.thumb_label.setText("⬇")
        
        if progress >= 100:
            # Keep thumbnail, just add green border/glow effect
            if self.thumb_label.pixmap() is None or self.thumb_label.pixmap().isNull():
                self.thumb_label.setText("✓")
            
            # Add green border to indicate success (keeps thumbnail visible)
            self.thumb_container.setStyleSheet(f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a1a, stop:1 #2a2a2a);
                border: 2px solid {COLOR_SUCCESS};
                border-radius: 10px;
            """)
            self.status_lbl.setText("✓ Completed")
            self.status_lbl.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 11px; background: transparent; font-weight: bold;")
            self.pbar.setStyleSheet(f"""
                QProgressBar {{ 
                    border: none; 
                    background: #2a2a2a; 
                    border-radius: 2px; 
                }}
                QProgressBar::chunk {{ 
                    background: {COLOR_SUCCESS};
                    border-radius: 2px; 
                }}
            """)
    
    def set_failed(self):
        # Keep thumbnail, just add red border
        if self.thumb_label.pixmap() is None or self.thumb_label.pixmap().isNull():
            self.thumb_label.setText("✗")
        
        self.thumb_container.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a1a, stop:1 #2a2a2a);
            border: 2px solid {COLOR_ERROR};
            border-radius: 10px;
        """)
        self.status_lbl.setText("✗ Failed")
        self.status_lbl.setStyleSheet(f"color: {COLOR_ERROR}; font-size: 11px; background: transparent;")

# --- MAIN APP ---

class MobileWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Downloader Pro")
        self.resize(430, 932)
        
        # Backend Init
        self.output_dir = str(Path.cwd() / "downloads")
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        self.manager = DownloadManager(output_dir=self.output_dir)
        self._connect_signals()
        self.active_widgets: Dict[str, ActivityRow] = {}
        self.pending_urls: List[str] = []  # URLs waiting to be processed
        
        # UI Init
        self.setStyleSheet(GLOBAL_STYLES)
        self._setup_ui()
        
        # Auto-paste clipboard after UI is ready
        QTimer.singleShot(100, self._auto_paste_clipboard)
        
    def _connect_signals(self):
        self.manager.signals.download_started.connect(self._on_start)
        self.manager.signals.progress_updated.connect(self._on_progress)
        self.manager.signals.download_completed.connect(self._on_complete)
        self.manager.signals.download_failed.connect(self._on_fail)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- PAGE STACK ---
        self.page_stack = QStackedWidget()
        
        # 1. HOME PAGE
        self.home_page = self._create_home_page()
        self.page_stack.addWidget(self.home_page)
        
        # 2. HISTORY PAGE
        self.history_page = self._create_history_page()
        self.page_stack.addWidget(self.history_page)
        
        # 3. SETTINGS PAGE
        self.settings_page = self._create_settings_page()
        self.page_stack.addWidget(self.settings_page)
        
        main_layout.addWidget(self.page_stack, 1)
        
        # --- BOTTOM NAVIGATION BAR ---
        self.nav_bar = self._create_nav_bar()
        main_layout.addWidget(self.nav_bar)
    
    def _create_nav_bar(self):
        """Create professional bottom navigation"""
        nav = QWidget()
        nav.setFixedHeight(80)
        nav.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_SURFACE};
                border-top: 1px solid {COLOR_BORDER};
            }}
        """)
        
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(10, 0, 10, 15)
        layout.setSpacing(0)
        
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        
        # Home
        self.nav_home = NavButton("⬇", "Download")
        self.nav_home.setChecked(True)
        self.nav_home.clicked.connect(lambda: self._switch_page(0))
        self.nav_group.addButton(self.nav_home)
        layout.addWidget(self.nav_home)
        
        # History
        self.nav_history = NavButton("📋", "History")
        self.nav_history.clicked.connect(lambda: self._switch_page(1))
        self.nav_group.addButton(self.nav_history)
        layout.addWidget(self.nav_history)
        
        # Settings
        self.nav_settings = NavButton("⚙", "Settings")
        self.nav_settings.clicked.connect(lambda: self._switch_page(2))
        self.nav_group.addButton(self.nav_settings)
        layout.addWidget(self.nav_settings)
        
        return nav
    
    def _switch_page(self, index):
        self.page_stack.setCurrentIndex(index)
        
        # Update nav button styles
        for btn in [self.nav_home, self.nav_history, self.nav_settings]:
            btn._update_style()
        
        # Refresh history when switching to it
        if index == 1:
            self._load_history()

    # --- PAGE CREATORS ---

    def _create_home_page(self):
        w = QWidget()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(20, 25, 20, 20)
        vbox.setSpacing(18)
        
        # Header with Logo
        header = QLabel("<span style='font-weight: 200;'>CYBERTRON</span><span style='color: #FF3131; font-weight: 800;'> DL</span>")
        header.setStyleSheet("font-size: 28px; letter-spacing: 3px; background: transparent;")
        vbox.addWidget(header)
        
        # --- INPUT CARD ---
        input_card = BentoCard()
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(18, 18, 18, 18)
        input_layout.setSpacing(14)
        
        # URL Header with counter
        url_header = QHBoxLayout()
        url_label = QLabel("Paste YouTube Links")
        url_label.setStyleSheet(f"color: {COLOR_TEXT_BODY}; font-size: 13px; font-weight: 500; background: transparent;")
        url_header.addWidget(url_label)
        url_header.addStretch()
        
        self.url_count_lbl = QLabel("")
        self.url_count_lbl.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 13px; font-weight: 600; background: transparent;")
        url_header.addWidget(self.url_count_lbl)
        input_layout.addLayout(url_header)
        
        # Text Input
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Paste URLs or text containing YouTube links here...")
        self.url_input.setMinimumHeight(110)
        self.url_input.setMaximumHeight(160)
        self.url_input.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.url_input)
        
        # Mode Selection Row
        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)
        
        self.mode_group = QButtonGroup(self)
        
        mode_btn_style = f"""
            QPushButton {{ 
                background: {COLOR_SURFACE_2}; 
                border: 1px solid {COLOR_BORDER}; 
                border-radius: 12px; 
                font-weight: 600;
            }}
            QPushButton:checked {{ 
                background: {COLOR_ACCENT}; 
                border: none; 
                color: white; 
            }}
            QPushButton:hover {{ 
                border-color: {COLOR_ACCENT}; 
            }}
        """
        
        self.audio_btn = QPushButton("🎵 Audio")
        self.audio_btn.setCheckable(True)
        self.audio_btn.setChecked(True)
        self.audio_btn.setFixedHeight(48)
        self.audio_btn.setStyleSheet(mode_btn_style)
        
        self.video_btn = QPushButton("🎬 Video")
        self.video_btn.setCheckable(True)
        self.video_btn.setFixedHeight(48)
        self.video_btn.setStyleSheet(mode_btn_style)
        
        self.mode_group.addButton(self.audio_btn, 0)
        self.mode_group.addButton(self.video_btn, 1)
        
        mode_row.addWidget(self.audio_btn, 1)
        mode_row.addWidget(self.video_btn, 1)
        
        # Format Combo
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "AAC", "WAV", "FLAC"])
        self.format_combo.setFixedHeight(48)
        self.format_combo.setFixedWidth(100)
        mode_row.addWidget(self.format_combo)
        
        input_layout.addLayout(mode_row)
        
        # Connect mode change
        self.video_btn.toggled.connect(self._on_mode_change)
        
        # Download Button
        self.download_btn = NeonButton("⬇  DOWNLOAD")
        self.download_btn.clicked.connect(self._start_download)
        input_layout.addWidget(self.download_btn)
        
        vbox.addWidget(input_card)
        
        # --- ACTIVE DOWNLOADS SECTION ---
        queue_header = QHBoxLayout()
        queue_title = QLabel("Active Downloads")
        queue_title.setStyleSheet("font-size: 18px; font-weight: 700; background: transparent;")
        queue_header.addWidget(queue_title)
        queue_header.addStretch()
        
        self.clear_btn = SecondaryButton("Clear")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.clicked.connect(self._clear_queue)
        queue_header.addWidget(self.clear_btn)
        
        vbox.addLayout(queue_header)
        
        # Queue Container
        self.queue_widget = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_widget)
        self.queue_layout.setSpacing(12)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        
        self.empty_queue_lbl = QLabel("No active downloads")
        self.empty_queue_lbl.setStyleSheet(f"color: {COLOR_TEXT_BODY}; font-style: italic; padding: 30px; background: transparent;")
        self.empty_queue_lbl.setAlignment(Qt.AlignCenter)
        self.queue_layout.addWidget(self.empty_queue_lbl)
        
        vbox.addWidget(self.queue_widget)
        vbox.addStretch()
        
        scroll.setWidget(content)
        
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        return w

    def _create_history_page(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(20, 25, 20, 20)
        vbox.setSpacing(18)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Download History")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        
        refresh_btn = SecondaryButton("↻ Refresh")
        refresh_btn.clicked.connect(self._load_history)
        header.addWidget(refresh_btn)
        
        vbox.addLayout(header)
        
        # History List
        self.hist_list = QListWidget()
        self.hist_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        vbox.addWidget(self.hist_list, 1)
        
        # Load history initially
        self._load_history()
        return w

    def _create_settings_page(self):
        w = QWidget()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(20, 25, 20, 20)
        vbox.setSpacing(22)
        
        # Header
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        vbox.addWidget(title)
        
        # --- Settings Card ---
        settings_card = BentoCard()
        card_layout = QVBoxLayout(settings_card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(20)
        
        # Save Location
        card_layout.addWidget(QLabel("Save Location", styleSheet=f"color: {COLOR_TEXT_BODY}; font-size: 13px; font-weight: 500; background: transparent;"))
        
        path_row = QHBoxLayout()
        self.path_input = QLineEdit(self.output_dir)
        self.path_input.setReadOnly(True)
        path_row.addWidget(self.path_input, 1)
        
        browse_btn = SecondaryButton("Browse")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_path)
        path_row.addWidget(browse_btn)
        card_layout.addLayout(path_row)
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLOR_BORDER};")
        card_layout.addWidget(divider)
        
        # Parallel Downloads
        card_layout.addWidget(QLabel("Parallel Downloads", styleSheet=f"color: {COLOR_TEXT_BODY}; font-size: 13px; font-weight: 500; background: transparent;"))
        
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(1, 5)
        self.spin_workers.setValue(3)
        self.spin_workers.setFixedHeight(50)
        self.spin_workers.valueChanged.connect(lambda v: self.manager.set_worker_count(v))
        card_layout.addWidget(self.spin_workers)
        
        # Divider
        divider2 = QFrame()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet(f"background-color: {COLOR_BORDER};")
        card_layout.addWidget(divider2)
        
        # Duplicate Handling
        card_layout.addWidget(QLabel("If File Exists", styleSheet=f"color: {COLOR_TEXT_BODY}; font-size: 13px; font-weight: 500; background: transparent;"))
        
        self.dup_combo = QComboBox()
        self.dup_combo.addItems(["Ask", "Skip", "Replace"])
        self.dup_combo.setFixedHeight(50)
        self.dup_combo.currentTextChanged.connect(lambda t: self.manager.set_duplicate_policy(t.lower()))
        card_layout.addWidget(self.dup_combo)
        
        vbox.addWidget(settings_card)
        vbox.addStretch()
        
        # Footer
        footer = QLabel("YouTube Downloader Pro v1.0\nCrafted by Cybertron")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"color: {COLOR_TEXT_BODY}; font-size: 13px; padding: 20px;")
        vbox.addWidget(footer)
        
        scroll.setWidget(content)
        
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        return w

    # --- LOGIC ---

    def _auto_paste_clipboard(self):
        """Automatically paste YouTube URLs from clipboard on app start"""
        try:
            clipboard = QGuiApplication.clipboard()
            text = clipboard.text()
            
            if text:
                urls = extract_youtube_urls(text)
                if urls:
                    self.url_input.setPlainText(text)
        except Exception as e:
            print(f"Clipboard access error: {e}")

    @Slot()
    def _on_text_changed(self):
        text = self.url_input.toPlainText()
        urls = extract_youtube_urls(text)
        count = len(urls)
        if count > 0:
            self.url_count_lbl.setText(f"✓ {count} link{'s' if count > 1 else ''} detected")
        else:
            self.url_count_lbl.setText("")

    @Slot(bool)
    def _on_mode_change(self, is_video):
        self.format_combo.clear()
        if is_video:
            self.format_combo.addItems(["MP4", "MKV", "WEBM"])
        else:
            self.format_combo.addItems(["MP3", "AAC", "WAV", "FLAC"])

    @Slot()
    def _start_download(self):
        text = self.url_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Input", "Please paste YouTube URLs first.")
            return
            
        urls = extract_youtube_urls(text)
        if not urls:
            QMessageBox.warning(self, "No URLs", "No valid YouTube links found in the text.")
            return
        
        # INSTANT FEEDBACK: Create pending entries immediately
        self.empty_queue_lbl.hide()
        self.pending_urls = urls.copy()
        
        for i, url in enumerate(urls):
            # Create immediate visual feedback with "Preparing..." status
            temp_id = f"pending_{hash(url)}_{i}"
            row = ActivityRow(temp_id, f"Preparing: {url[:50]}...", "Connecting...")
            self.active_widgets[temp_id] = row
            self.queue_layout.insertWidget(0, row)
        
        # Disable button during processing
        self.download_btn.set_loading(True)
        self.download_btn.setText("PROCESSING...")
        
        mode = DownloadMode.VIDEO if self.video_btn.isChecked() else DownloadMode.AUDIO
        fmt = self.format_combo.currentText().lower()
        
        self.manager.set_worker_count(self.spin_workers.value())
        
        for url in urls:
            self.manager.add_url(url, mode, "best", 0, fmt)
        
        self.manager.start()
        
        # Clear input after adding to queue
        self.url_input.clear()
        self.url_count_lbl.setText("")
        
        # Re-enable button after short delay
        QTimer.singleShot(1500, self._reset_download_btn)
    
    def _reset_download_btn(self):
        self.download_btn.set_loading(False)
        self.download_btn.setText("⬇  DOWNLOAD")

    def _load_history(self):
        self.hist_list.clear()
        history = self.manager.get_history()
        
        if not history:
            item = QListWidgetItem("No download history yet")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.hist_list.addItem(item)
            return
        
        for h in history:
            title = h.get('title', 'Unknown')
            mode = h.get('mode', 'audio').upper()
            ts = h.get('timestamp', '')[:16].replace('T', ' ')
            status = h.get('status', 'completed')
            
            icon = "✓" if status == "completed" else "✗"
            color = COLOR_SUCCESS if status == "completed" else COLOR_ERROR
            
            item = QListWidgetItem(f"{icon} {title}\n   {mode} • {ts}")
            self.hist_list.addItem(item)

    def _browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.output_dir)
        if folder:
            self.output_dir = folder
            self.path_input.setText(folder)
            self.manager.set_output_dir(folder)

    def _clear_queue(self):
        for item_id, widget in list(self.active_widgets.items()):
            widget.setParent(None)
            widget.deleteLater()
        self.active_widgets.clear()
        self.empty_queue_lbl.show()

    # --- DOWNLOAD SIGNALS ---

    @Slot(str, str, str)
    def _on_start(self, item_id, title, thumbnail_url):
        print(f"Download started: {title}")
        
        # Remove pending placeholder entries
        pending_to_remove = [k for k in self.active_widgets.keys() if k.startswith("pending_")]
        for pid in pending_to_remove:
            if pid in self.active_widgets:
                widget = self.active_widgets.pop(pid)
                widget.setParent(None)
                widget.deleteLater()
        
        self.empty_queue_lbl.hide()
        
        # Add real download entry with thumbnail
        if item_id not in self.active_widgets:
            row = ActivityRow(item_id, title, "Starting download...", thumbnail_url)
            self.active_widgets[item_id] = row
            self.queue_layout.insertWidget(0, row)

    @Slot(str, float, str)
    def _on_progress(self, item_id, progress, status):
        if item_id in self.active_widgets:
            self.active_widgets[item_id].update_progress(progress, status)

    @Slot(str, str, str)
    def _on_complete(self, item_id, title, path):
        if item_id in self.active_widgets:
            self.active_widgets[item_id].update_progress(100, "Completed")
        self._load_history()

    @Slot(str, str, str)
    def _on_fail(self, item_id, title, error):
        if item_id in self.active_widgets:
            self.active_widgets[item_id].set_failed()

    def closeEvent(self, event):
        self.manager.stop()
        super().closeEvent(event)
