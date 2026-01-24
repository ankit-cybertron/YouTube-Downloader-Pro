import sys
import os
import requests
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QStackedWidget, QFrame, QGraphicsDropShadowEffect,
    QScrollArea, QApplication, QListWidget, QListWidgetItem,
    QMessageBox, QCheckBox, QAbstractItemView, QFileDialog, QTextEdit
)
from PySide6.QtCore import Qt, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor, QFont

from src.core.worker import DownloadManager, DownloadMode
from src.core.utils import extract_youtube_urls, resource_path
from src.desktop.ui.components import DownloadCard

# --- THEME CONSTANTS ---
COLOR_BG_MAIN = "#F5F5F7"      # Light gray background
COLOR_BG_SIDEBAR = "#FFFFFF"   # White sidebar
COLOR_BG_CARD = "#FFFFFF"      # White cards
COLOR_ACCENT = "#FF3B5C"       # Vibrant Red/Pink
COLOR_ACCENT_HOVER = "#E63552"
COLOR_TEXT_MAIN = "#333333"
COLOR_TEXT_SUB = "#888888"
COLOR_BORDER = "#E0E0E0"

APP_VERSION = "v2.1.0"
GITHUB_REPO = "ankit-cybertron/YouTube-Downloader-Pro"

STYLE_SHEET = f"""
    QMainWindow {{
        background-color: {COLOR_BG_MAIN};
    }}
    QWidget {{
        font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
        color: {COLOR_TEXT_MAIN};
        font-size: 14px;
    }}
    
    /* Sidebar */
    QFrame#sidebar {{
        background-color: {COLOR_BG_SIDEBAR};
        border-right: 1px solid {COLOR_BORDER};
    }}
    
    /* Sidebar List */
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
        margin-top: 20px;
    }}
    QListWidget::item {{
        height: 50px;
        padding-left: 20px;
        color: {COLOR_TEXT_SUB};
        border-left: 3px solid transparent;
        margin-bottom: 5px;
    }}
    QListWidget::item:selected {{
        color: {COLOR_ACCENT};
        background-color: #FEF2F4;
        border-left: 3px solid {COLOR_ACCENT};
        font-weight: 600;
    }}
    QListWidget::item:hover:!selected {{
        background-color: #F8F8F8;
        color: {COLOR_TEXT_MAIN};
    }}
    
    /* Inputs */
    QLineEdit, QTextEdit, QComboBox, QSpinBox {{
        padding: 12px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        background-color: {COLOR_BG_CARD};
        selection-background-color: {COLOR_ACCENT};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {COLOR_ACCENT};
    }}
    
    /* Buttons */
    QPushButton {{
        border-radius: 8px;
        padding: 10px 20px;
        border: 1px solid {COLOR_BORDER};
        background-color: {COLOR_BG_CARD};
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: #FAFAFA;
        border-color: #CCC;
    }}
    
    QPushButton#primaryBtn {{
        background-color: {COLOR_ACCENT};
        color: white;
        border: none;
    }}
    QPushButton#primaryBtn:hover {{
        background-color: {COLOR_ACCENT_HOVER};
    }}
    QPushButton#primaryBtn:disabled {{
        background-color: #FFB3C0;
    }}
    
    /* Cards */
    QFrame#card {{
        background-color: {COLOR_BG_CARD};
        border-radius: 12px;
        border: 1px solid {COLOR_BORDER};
    }}
    
    /* Headers */
    QLabel#pageTitle {{
        font-size: 24px;
        font-weight: 700;
        color: {COLOR_TEXT_MAIN};
    }}
    QLabel#sectionTitle {{
        font-size: 16px;
        font-weight: 600;
        color: {COLOR_TEXT_MAIN};
        margin-bottom: 8px;
    }}
    
    /* ScrollArea */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader Pro")
        self.resize(1100, 750)
        self.setStyleSheet(STYLE_SHEET)
        
        # Backend
        self.download_path = str(Path.home() / "Downloads" / "YT-Downloader")
        self.manager = DownloadManager(output_dir=self.download_path)
        self.download_widgets = {}
        
        # UI Setup
        self._init_ui()
        self._connect_signals()
        
        # State
        self.current_metadata = None

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- SIDEBAR ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 20)
        
        # App Logo/Title
        title_box = QLabel("YT PRO")
        title_box.setAlignment(Qt.AlignCenter)
        title_box.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_ACCENT}; padding: 30px 0;")
        sb_layout.addWidget(title_box)
        
        # Nav List
        self.nav = QListWidget()
        self.nav.addItem("  New Download")
        self.nav.addItem("  Active Queue")
        self.nav.addItem("  History")
        self.nav.addItem("  Settings")
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self.switch_tab)
        sb_layout.addWidget(self.nav)
        
        # Version
        ver = QLabel("v2.1.0")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(f"color: {COLOR_TEXT_SUB}; font-size: 11px;")
        sb_layout.addWidget(ver)
        
        main_layout.addWidget(sidebar)
        
        # --- CONTENT ---
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_download_tab())  # Index 0
        self.stack.addWidget(self._create_queue_tab())     # Index 1
        self.stack.addWidget(self._create_history_tab())   # Index 2
        self.stack.addWidget(self._create_settings_tab())  # Index 3
        
        main_layout.addWidget(self.stack)

    # --- TABS ---
    
    def _create_download_tab(self):
        """Home tab with search and result view."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Inner stack for Search vs Details state
        self.dl_stack = QStackedWidget()
        
        # 1. Search View
        search_view = QWidget()
        sl = QVBoxLayout(search_view)
        sl.setAlignment(Qt.AlignCenter)
        
        # Search Card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(700, 180) # Increased height slightly
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0,15))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)
        
        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 25, 30, 25)
        
        # Header text
        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Paste Video Links or Text", styleSheet=f"color:{COLOR_TEXT_SUB}; font-weight:600;"))
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: 700; background-color: #FEF2F4; padding: 2px 8px; border-radius: 4px;")
        self.lbl_count.hide()
        header_row.addWidget(self.lbl_count)
        header_row.addStretch()
        cl.addLayout(header_row)
        
        # Input Row
        row = QHBoxLayout()
        
        # Multi-line input for "Smart Detection"
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Paste text containing YouTube links here...")
        self.url_input.setFixedHeight(60) # height for ~2 lines
        self.url_input.textChanged.connect(self._check_input_count)
        self.url_input.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 8px;
                background-color: {COLOR_BG_CARD};
                font-size: 14px;
            }}
            QTextEdit:focus {{
                border: 1px solid {COLOR_ACCENT};
            }}
        """)
        row.addWidget(self.url_input)
        
        btn_go = QPushButton("Analyze")
        btn_go.setObjectName("primaryBtn")
        btn_go.setFixedWidth(100)
        btn_go.setFixedHeight(60)
        btn_go.setCursor(Qt.PointingHandCursor)
        btn_go.clicked.connect(self._process_input)
        row.addWidget(btn_go)
        
        cl.addLayout(row)
        sl.addWidget(card)
        
        # Helper text removed for cleaner UI
        # info = QLabel("Smart Mode: Paste paragraphs of text, we'll extract all links automatically.")
        # info.setStyleSheet("color: #999; margin-top: 10px;")
        # sl.addWidget(info)
        
        self.dl_stack.addWidget(search_view)
        
        # 2. Loading View
        loading_view = QWidget()
        ll = QVBoxLayout(loading_view)
        ll.setAlignment(Qt.AlignCenter)
        self.lbl_loading = QLabel("Fetching Metadata...")
        self.lbl_loading.setStyleSheet(f"font-size: 18px; color: {COLOR_TEXT_MAIN}; font-weight: 600;")
        ll.addWidget(self.lbl_loading)
        self.dl_stack.addWidget(loading_view)
        
        # 3. Result View (The "Clean Info Card" from before)
        result_view = QWidget()
        rl = QVBoxLayout(result_view)
        rl.setContentsMargins(40, 40, 40, 40)
        # ... (Same card logic as previous step)
        
        # Back nav
        nav_row = QHBoxLayout()
        btn_back = QPushButton("← Back to Search")
        btn_back.setStyleSheet("border:none; color: #666; text-align:left;")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.dl_stack.setCurrentIndex(0))
        nav_row.addWidget(btn_back)
        nav_row.addStretch()
        rl.addLayout(nav_row)
        
        # Detail Card
        d_card = QFrame()
        d_card.setObjectName("card")
        d_card.setFixedSize(900, 450)
        dl_layout = QHBoxLayout(d_card)
        dl_layout.setContentsMargins(30, 30, 30, 30)
        
        # Left Info
        left = QVBoxLayout()
        self.img_thumb = QLabel()
        self.img_thumb.setFixedSize(400, 225)
        self.img_thumb.setStyleSheet("background-color: #EEE; border-radius: 8px;")
        self.img_thumb.setScaledContents(True)
        left.addWidget(self.img_thumb)
        
        self.lbl_title = QLabel("Title")
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; margin-top: 10px;")
        left.addWidget(self.lbl_title)
        
        self.lbl_meta = QLabel("Channel • 10:00")
        self.lbl_meta.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: 600;")
        left.addWidget(self.lbl_meta)
        left.addStretch()
        
        dl_layout.addLayout(left, 5)
        
        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #EEE;")
        dl_layout.addWidget(div)
        
        # Right Options
        right = QVBoxLayout()
        right.setContentsMargins(20, 0, 0, 0)
        right.addWidget(QLabel("Download Options", styleSheet="font-size:16px; font-weight:700;"))
        right.addSpacing(20)
        
        self.combo_fmt = QComboBox()
        right.addWidget(QLabel("Format / Quality"))
        right.addWidget(self.combo_fmt)
        
        right.addStretch()
        
        self.btn_dl_now = QPushButton("Download Now")
        self.btn_dl_now.setObjectName("primaryBtn")
        self.btn_dl_now.setFixedHeight(50)
        self.btn_dl_now.setCursor(Qt.PointingHandCursor)
        self.btn_dl_now.clicked.connect(self._start_single_download)
        right.addWidget(self.btn_dl_now)
        
        dl_layout.addLayout(right, 4)
        
        rl.addWidget(d_card, alignment=Qt.AlignTop | Qt.AlignHCenter)
        rl.addStretch()
        
        self.dl_stack.addWidget(result_view)
        
        layout.addWidget(self.dl_stack)
        return container

    def _create_queue_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        head = QHBoxLayout()
        head.addWidget(QLabel("Active Queue", objectName="pageTitle"))
        head.addStretch()
        
        btn_clear = QPushButton("Clear Completed")
        btn_clear.clicked.connect(self._clear_queue)
        head.addWidget(btn_clear)
        layout.addLayout(head)
        
        # Scroll List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setAlignment(Qt.AlignTop)
        self.queue_layout.setSpacing(10)
        
        scroll.setWidget(self.queue_container)
        layout.addWidget(scroll)
        
        return tab

    def _create_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(40, 40, 40, 40)
        
        head = QHBoxLayout()
        head.addWidget(QLabel("Download History", objectName="pageTitle"))
        head.addStretch()
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_history)
        head.addWidget(btn_ref)
        layout.addLayout(head)
        
        self.hist_list = QListWidget()
        self.hist_list.setFrameShape(QFrame.NoFrame)
        self.hist_list.setStyleSheet("background: transparent;")
        layout.addWidget(self.hist_list)
        
        self._load_history()
        return tab

    def _create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignTop)
        
        layout.addWidget(QLabel("Settings", objectName="pageTitle"))
        layout.addSpacing(20)
        
        # Card style settings
        group = QFrame()
        group.setObjectName("card")
        gl = QVBoxLayout(group)
        gl.setSpacing(20)
        gl.setContentsMargins(20, 20, 20, 20)
        
        # Output Path
        gl.addWidget(QLabel("Output Folder", objectName="sectionTitle"))
        row = QHBoxLayout()
        self.txt_path = QLineEdit(self.download_path)
        self.txt_path.setReadOnly(True)
        row.addWidget(self.txt_path)
        btn_browse = QPushButton("Change")
        btn_browse.clicked.connect(self._select_folder)
        row.addWidget(btn_browse)
        gl.addLayout(row)
        
        # Concurrent
        gl.addWidget(QLabel("Concurrent Downloads", objectName="sectionTitle"))
        row2 = QHBoxLayout()
        spin = QSpinBox()
        spin.setRange(1, 10)
        spin.setValue(3)
        spin.setFixedWidth(100)
        spin.valueChanged.connect(lambda v: self.manager.set_worker_count(v))
        row2.addWidget(spin)
        row2.addWidget(QLabel("(Max simultaneous downloads)"))
        gl.addLayout(row2)
        
        # Updates
        gl.addWidget(QLabel("Updates", objectName="sectionTitle"))
        u_row = QHBoxLayout()
        u_row.addWidget(QLabel(f"Current Version: {APP_VERSION}", styleSheet="color: #666;"))
        u_row.addStretch()
        btn_upd = QPushButton("Check for Updates")
        btn_upd.setCursor(Qt.PointingHandCursor)
        btn_upd.clicked.connect(self._check_for_updates)
        u_row.addWidget(btn_upd)
        gl.addLayout(u_row)
        
        layout.addWidget(group)
        return tab

    # --- LOGIC ---
    
    def _connect_signals(self):
        self.manager.signals.progress_updated.connect(self._on_progress)
        self.manager.signals.download_completed.connect(self._on_completed)
        self.manager.signals.download_failed.connect(self._on_failed)
        self.manager.signals.download_started.connect(self._on_started)

    def switch_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        if idx == 2:
            self._load_history()

    @Slot()
    def _check_input_count(self):
        text = self.url_input.toPlainText()
        urls = extract_youtube_urls(text)
        count = len(urls)
        
        if count > 0:
            self.lbl_count.setText(f"{count} Link{'s' if count > 1 else ''} Found")
            self.lbl_count.show()
        else:
            self.lbl_count.hide()

    @Slot()
    def _process_input(self):
        text = self.url_input.toPlainText().strip()
        if not text:
            return
            
        urls = extract_youtube_urls(text)
        
        if len(urls) == 0:
            QMessageBox.warning(self, "Invalid URL", "No YouTube links found in the text.")
            return
            
        # If multiple URLs or Playlist -> Batch Mode (Add directly to queue)
        if len(urls) > 1 or "playlist" in text.lower():
            confirm = QMessageBox.question(
                self, "Batch Download", 
                f"Detected {len(urls)} link(s) or playlist.\nAdd all to queue immediately?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self._start_batch(urls)
        else:
            # Single Video -> Show Details Metadata Screen
            self._fetch_metadata(urls[0])

    def _fetch_metadata(self, url):
        self.dl_stack.setCurrentIndex(1) # Loading
        self.manager.fetch_metadata(url, self._on_meta_success, self._on_meta_error)

    def _on_meta_success(self, info):
        self.current_metadata = info
        
        # Update UI
        self.lbl_title.setText(info.get('title', 'Unknown'))
        channel = info.get('uploader', 'Unknown')
        dur = info.get('duration_string') or "--:--"
        self.lbl_meta.setText(f"{channel}  •  {dur}")
        
        # Load Thumb
        t_url = info.get('thumbnail')
        if t_url:
            self._load_thumb(t_url)
            
        # Formats
        self.combo_fmt.clear()
        opts = [
            ("Video MP4 (1080p)", "video", "1080p", "mp4"),
            ("Video MP4 (720p)", "video", "720p", "mp4"),
            ("Video MP4 (480p)", "video", "480p", "mp4"),
            ("Audio MP3 (Best)", "audio", "best", "mp3"),
        ]
        for l, m, q, f in opts:
            self.combo_fmt.addItem(l, (m, q, f))
            
        self.dl_stack.setCurrentIndex(2) # Result page

    def _on_meta_error(self, err):
        self.dl_stack.setCurrentIndex(0)
        QMessageBox.warning(self, "Error", f"Failed to fetch info: {err}")

    def _start_single_download(self):
        if not self.current_metadata: 
            return
        
        data = self.combo_fmt.currentData() # (mode, qual, fmt)
        url = self.current_metadata.get('webpage_url')
        title = self.current_metadata.get('title')
        
        self.manager.add_download(url, data[0], data[1], data[2], title)
        
        # Go to queue
        self.nav.setCurrentRow(1)
        self.dl_stack.setCurrentIndex(0) # Reset home
        self.url_input.clear()

    def _start_batch(self, urls):
        # Add all with defaults (Video 1080p for now, or could ask)
        for url in urls:
            # Defaulting to Best Video
            self.manager.add_download(url, "video", "best", "mp4")
            
        self.nav.setCurrentRow(1) # Switch to queue
        self.url_input.clear()

    def _load_thumb(self, url):
        try:
            data = requests.get(url, timeout=3).content
            pix = QPixmap()
            pix.loadFromData(data)
            self.img_thumb.setPixmap(pix)
        except:
            pass

    # Worker Signals
    def _on_started(self, item_id, title, thumb):
        # Create card widget
        card = DownloadCard(item_id, title)
        self.queue_layout.insertWidget(0, card)
        self.download_widgets[item_id] = card

    def _on_progress(self, item_id, val, text):
        if item_id in self.download_widgets:
            self.download_widgets[item_id].update_progress(val, text)

    def _on_completed(self, item_id, title, path):
        if item_id in self.download_widgets:
            self.download_widgets[item_id].set_completed()

    def _on_failed(self, item_id, title, err):
        if item_id in self.download_widgets:
            self.download_widgets[item_id].set_failed(err)

    def _select_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder", self.download_path)
        if d:
            self.download_path = d
            self.txt_path.setText(d)
            self.manager.set_output_dir(d)

    def _load_history(self):
        self.hist_list.clear()
        data = self.manager.get_history()
        for idx, item in enumerate(data):
            # Create a nice item
            title = item.get('title', 'Unknown')
            w = QListWidgetItem(f"{idx+1}. {title}")
            self.hist_list.addItem(w)

    def _clear_queue(self):
        # Remove widgets that are done (simple logic)
        for i in reversed(range(self.queue_layout.count())):
            w = self.queue_layout.itemAt(i).widget()
            if isinstance(w, DownloadCard):
                w.deleteLater()
        self.download_widgets.clear()

    def _check_for_updates(self):
        """Check GitHub for new release."""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            resp = requests.get(url, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").strip()
                
                # Check match (e.g. v2.1.0 vs v2.1.0)
                if latest_tag and latest_tag != APP_VERSION:
                    reply = QMessageBox.question(
                        self, "Update Available",
                        f"A new version ({latest_tag}) is available!\n\n"
                        "Would you like to open the download page?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        webbrowser.open(data.get("html_url", "https://github.com/" + GITHUB_REPO))
                else:
                    QMessageBox.information(self, "Up to Date", f"You are using the latest version ({APP_VERSION}).")
            else:
                QMessageBox.warning(self, "Check Failed", "Could not connect to update server.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Update check failed: {str(e)}")

