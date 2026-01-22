#!/usr/bin/env python3
"""
app.py - YouTube Downloader Pro

A modern, minimal macOS desktop application for downloading YouTube content.
Built with PySide6 (Qt 6) and yt-dlp.

Features:
- Clean tabbed interface
- Audio/Video download modes
- Video quality selection
- Parallel downloads with pause/resume
- Download history
- Dark mode UI
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QSpinBox,
    QProgressBar, QFileDialog, QRadioButton, QButtonGroup,
    QListWidget, QListWidgetItem, QFrame, QMessageBox,
    QTabWidget, QScrollArea, QSizePolicy, QStackedWidget, QDialog
)
from PySide6.QtCore import Qt, Slot, QTimer, QSize
from PySide6.QtGui import QPalette, QColor, QFont

from worker import DownloadManager, DownloadMode


class DuplicateDialog(QDialog):
    """Dialog for handling duplicate files."""
    
    # Return codes
    SKIP = 0
    REPLACE = 1
    SKIP_ALL = 2
    REPLACE_ALL = 3
    
    def __init__(self, duplicates: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Files Found")
        self.setMinimumWidth(500)
        self.result_action = self.SKIP
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        count = len(duplicates)
        header = QLabel(f"Found {count} file{'s' if count > 1 else ''} already in downloads folder:")
        header.setFont(QFont("SF Pro Text", 14, QFont.Bold))
        layout.addWidget(header)
        
        # File list
        file_list = QListWidget()
        file_list.setMaximumHeight(150)
        for dup in duplicates[:10]:  # Show max 10
            file_list.addItem(dup)
        if count > 10:
            file_list.addItem(f"... and {count - 10} more")
        layout.addWidget(file_list)
        
        # Question
        question = QLabel("What would you like to do?")
        question.setFont(QFont("SF Pro Text", 13))
        layout.addWidget(question)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        skip_btn = QPushButton("Skip")
        skip_btn.clicked.connect(lambda: self._set_result(self.SKIP))
        btn_layout.addWidget(skip_btn)
        
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(lambda: self._set_result(self.REPLACE))
        btn_layout.addWidget(replace_btn)
        
        if count > 1:
            skip_all_btn = QPushButton("Skip All")
            skip_all_btn.clicked.connect(lambda: self._set_result(self.SKIP_ALL))
            btn_layout.addWidget(skip_all_btn)
            
            replace_all_btn = QPushButton("Replace All")
            replace_all_btn.clicked.connect(lambda: self._set_result(self.REPLACE_ALL))
            btn_layout.addWidget(replace_all_btn)
        
        layout.addLayout(btn_layout)
    
    def _set_result(self, action: int):
        self.result_action = action
        self.accept()


def extract_youtube_urls(text: str) -> List[str]:
    """
    Extract YouTube URLs from any text input.
    Handles various YouTube URL formats:
    - youtube.com/watch?v=
    - youtu.be/
    - youtube.com/playlist?list=
    - youtube.com/shorts/
    - youtube.com/@channel
    - youtube.com/channel/
    """
    patterns = [
        # Standard watch URLs
        r'https?://(?:www\.)?youtube\.com/watch\?[^\s<>"\']+',
        # Short URLs
        r'https?://youtu\.be/[a-zA-Z0-9_-]+(?:\?[^\s<>"\']*)?',
        # Playlist URLs
        r'https?://(?:www\.)?youtube\.com/playlist\?[^\s<>"\']+',
        # Shorts
        r'https?://(?:www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]+',
        # Channel URLs
        r'https?://(?:www\.)?youtube\.com/@[^\s<>"\'/]+',
        r'https?://(?:www\.)?youtube\.com/channel/[^\s<>"\']+',
        r'https?://(?:www\.)?youtube\.com/c/[^\s<>"\']+',
        # Music URLs
        r'https?://music\.youtube\.com/watch\?[^\s<>"\']+',
    ]
    
    urls = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        # Clean URL (remove trailing punctuation)
        url = url.rstrip('.,;:!?')
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls



class DownloadCard(QFrame):
    """Modern card widget for individual download progress."""
    
    def __init__(self, item_id: str, title: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.setObjectName("downloadCard")
        self.setFixedHeight(72)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Title row
        title_row = QHBoxLayout()
        self.title_label = QLabel(title[:50] + "..." if len(title) > 50 else title)
        self.title_label.setFont(QFont("SF Pro Text", 13, QFont.Medium))
        title_row.addWidget(self.title_label)
        
        self.status_label = QLabel("Waiting...")
        self.status_label.setFont(QFont("SF Pro Text", 11))
        self.status_label.setStyleSheet("color: #8e8e93;")
        title_row.addWidget(self.status_label, alignment=Qt.AlignRight)
        layout.addLayout(title_row)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        layout.addWidget(self.progress_bar)
    
    def update_progress(self, progress: float, status: str):
        self.progress_bar.setValue(int(progress))
        self.status_label.setText(status)
    
    def set_completed(self):
        self.progress_bar.setValue(100)
        self.status_label.setText("✓ Done")
        self.status_label.setStyleSheet("color: #30d158;")
    
    def set_failed(self, error: str):
        self.status_label.setText("✗ Failed")
        self.status_label.setStyleSheet("color: #ff453a;")


class MainWindow(QMainWindow):
    """Main application window with modern tabbed interface."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("YouTube Downloader Pro")
        self.setMinimumSize(700, 550)
        self.resize(800, 600)
        
        # Set window icon
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Default paths
        self.output_dir = str(Path(__file__).parent / "downloads")
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Download manager
        self.manager = DownloadManager(output_dir=self.output_dir)
        self._connect_signals()
        
        # Track widgets
        self.download_cards: Dict[str, DownloadCard] = {}
        
        # Setup
        self._setup_ui()
        self._apply_modern_theme()
    
    def _connect_signals(self):
        self.manager.signals.progress_updated.connect(self._on_progress_updated)
        self.manager.signals.download_started.connect(self._on_download_started)
        self.manager.signals.download_completed.connect(self._on_download_completed)
        self.manager.signals.download_failed.connect(self._on_download_failed)
        self.manager.signals.download_skipped.connect(self._on_download_skipped)
        self.manager.signals.log_message.connect(self._on_log_message)
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.tabs.addTab(self._create_download_tab(), "Download")
        self.tabs.addTab(self._create_queue_tab(), "Queue")
        self.tabs.addTab(self._create_history_tab(), "History")
        self.tabs.addTab(self._create_settings_tab(), "Settings")
    
    def _create_download_tab(self) -> QWidget:
        """Main download tab - clean and minimal with smart URL detection."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Download")
        header.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        layout.addWidget(header)
        
        # URL Input with helper text
        url_header = QHBoxLayout()
        url_label = QLabel("Paste any text containing YouTube links")
        url_label.setFont(QFont("SF Pro Text", 13))
        url_label.setStyleSheet("color: #8e8e93;")
        url_header.addWidget(url_label)
        
        url_header.addStretch()
        
        # Detected URLs counter
        self.url_count_label = QLabel("")
        self.url_count_label.setFont(QFont("SF Pro Text", 12))
        self.url_count_label.setStyleSheet("color: #30d158;")
        url_header.addWidget(self.url_count_label)
        
        layout.addLayout(url_header)
        
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText(
            "Paste URLs, text, or paragraphs here...\n\n"
            "Examples:\n"
            "• https://youtube.com/watch?v=...\n"
            "• https://youtu.be/...\n"
            "• Playlist: https://youtube.com/playlist?list=...\n"
            "• Channel: https://youtube.com/@channelname\n\n"
            "The app will automatically detect all YouTube links!"
        )
        self.url_input.setMinimumHeight(120)
        self.url_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.url_input)
        
        # Mode selection row
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(24)
        
        # Mode buttons
        self.mode_group = QButtonGroup(self)
        
        mode_container = QHBoxLayout()
        mode_container.setSpacing(16)
        
        self.audio_btn = QPushButton("Audio")
        self.audio_btn.setCheckable(True)
        self.audio_btn.setChecked(True)
        self.audio_btn.setFixedSize(100, 40)
        mode_container.addWidget(self.audio_btn)
        
        self.video_btn = QPushButton("Video")
        self.video_btn.setCheckable(True)
        self.video_btn.setFixedSize(100, 40)
        mode_container.addWidget(self.video_btn)
        
        self.mode_group.addButton(self.audio_btn, 0)
        self.mode_group.addButton(self.video_btn, 1)
        
        mode_layout.addLayout(mode_container)
        mode_layout.addStretch()
        
        # Audio format dropdown
        audio_format_container = QHBoxLayout()
        audio_format_container.setSpacing(8)
        
        audio_format_label = QLabel("Format:")
        audio_format_label.setFont(QFont("SF Pro Text", 13))
        audio_format_container.addWidget(audio_format_label)
        
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["MP3", "AAC", "WAV", "FLAC"])
        self.audio_format_combo.setFixedWidth(80)
        audio_format_container.addWidget(self.audio_format_combo)
        
        mode_layout.addLayout(audio_format_container)
        
        # Video format dropdown
        video_format_container = QHBoxLayout()
        video_format_container.setSpacing(8)
        
        video_format_label = QLabel("Format:")
        video_format_label.setFont(QFont("SF Pro Text", 13))
        video_format_container.addWidget(video_format_label)
        
        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems(["MP4", "MKV", "WEBM"])
        self.video_format_combo.setFixedWidth(80)
        self.video_format_combo.setEnabled(False)
        video_format_container.addWidget(self.video_format_combo)
        
        mode_layout.addLayout(video_format_container)
        
        # Quality dropdown (for video)
        quality_container = QHBoxLayout()
        quality_container.setSpacing(8)
        
        quality_label = QLabel("Quality:")
        quality_label.setFont(QFont("SF Pro Text", 13))
        quality_container.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Best", "1080p", "720p", "480p", "360p"])
        self.quality_combo.setEnabled(False)
        self.quality_combo.setFixedWidth(100)
        quality_container.addWidget(self.quality_combo)
        
        mode_layout.addLayout(quality_container)
        layout.addLayout(mode_layout)
        
        # Connect mode toggle
        def on_mode_changed(is_video):
            self.quality_combo.setEnabled(is_video)
            self.video_format_combo.setEnabled(is_video)
            self.audio_format_combo.setEnabled(not is_video)
        
        self.video_btn.toggled.connect(on_mode_changed)
        
        layout.addStretch()
        
        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedHeight(50)
        self.download_btn.setFont(QFont("SF Pro Text", 15, QFont.Medium))
        self.download_btn.clicked.connect(self._on_start)
        layout.addWidget(self.download_btn)
        
        return tab
    
    @Slot()
    def _on_text_changed(self):
        """Update detected URL count when text changes."""
        text = self.url_input.toPlainText()
        urls = extract_youtube_urls(text)
        count = len(urls)
        
        if count == 0:
            self.url_count_label.setText("")
        elif count == 1:
            self.url_count_label.setText("1 link detected")
        else:
            self.url_count_label.setText(f"{count} links detected")
    
    def _create_queue_tab(self) -> QWidget:
        """Queue tab - shows active downloads."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        # Header row
        header_row = QHBoxLayout()
        
        header = QLabel("Queue")
        header.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        header_row.addWidget(header)
        
        header_row.addStretch()
        
        # Control buttons
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFixedSize(80, 36)
        self.pause_btn.clicked.connect(self._on_pause)
        header_row.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setFixedSize(80, 36)
        self.resume_btn.setEnabled(False)
        self.resume_btn.clicked.connect(self._on_resume)
        header_row.addWidget(self.resume_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(80, 36)
        self.clear_btn.clicked.connect(self._on_clear)
        header_row.addWidget(self.clear_btn)
        
        layout.addLayout(header_row)
        
        # Downloads list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(8)
        self.queue_layout.addStretch()
        
        # Empty state
        self.empty_label = QLabel("No active downloads")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #8e8e93; font-size: 15px;")
        self.queue_layout.insertWidget(0, self.empty_label)
        
        scroll.setWidget(self.queue_container)
        layout.addWidget(scroll, 1)
        
        # Log output (collapsible)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setPlaceholderText("Log output...")
        layout.addWidget(self.log_output)
        
        return tab
    
    def _create_history_tab(self) -> QWidget:
        """History tab - shows recent downloads."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        header = QLabel("History")
        header.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        layout.addWidget(header)
        
        self.history_list = QListWidget()
        self.history_list.setSpacing(4)
        layout.addWidget(self.history_list, 1)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._refresh_history)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)
        
        # Load history
        self._refresh_history()
        
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """Settings tab - configuration options."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        header = QLabel("Settings")
        header.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        layout.addWidget(header)
        
        # Output folder
        folder_section = QVBoxLayout()
        folder_section.setSpacing(8)
        
        folder_label = QLabel("Output Folder")
        folder_label.setFont(QFont("SF Pro Text", 13))
        folder_label.setStyleSheet("color: #8e8e93;")
        folder_section.addWidget(folder_label)
        
        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit(self.output_dir)
        self.folder_input.setReadOnly(True)
        folder_row.addWidget(self.folder_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._on_browse_folder)
        folder_row.addWidget(browse_btn)
        folder_section.addLayout(folder_row)
        
        layout.addLayout(folder_section)
        
        # Parallel downloads
        workers_section = QHBoxLayout()
        workers_section.setSpacing(16)
        
        workers_label = QLabel("Parallel Downloads")
        workers_label.setFont(QFont("SF Pro Text", 14))
        workers_section.addWidget(workers_label)
        
        workers_section.addStretch()
        
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 5)
        self.workers_spin.setValue(3)
        self.workers_spin.setFixedWidth(80)
        workers_section.addWidget(self.workers_spin)
        
        layout.addLayout(workers_section)
        
        # Speed limit
        speed_section = QHBoxLayout()
        speed_section.setSpacing(16)
        
        speed_label = QLabel("Speed Limit")
        speed_label.setFont(QFont("SF Pro Text", 14))
        speed_section.addWidget(speed_label)
        
        speed_section.addStretch()
        
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 100000)
        self.speed_spin.setValue(0)
        self.speed_spin.setSuffix(" KB/s")
        self.speed_spin.setSpecialValueText("Unlimited")
        self.speed_spin.setFixedWidth(120)
        speed_section.addWidget(self.speed_spin)
        
        layout.addLayout(speed_section)
        
        # Duplicate file handling
        duplicate_section = QHBoxLayout()
        duplicate_section.setSpacing(16)
        
        duplicate_label = QLabel("If file exists")
        duplicate_label.setFont(QFont("SF Pro Text", 14))
        duplicate_section.addWidget(duplicate_label)
        
        duplicate_section.addStretch()
        
        self.duplicate_combo = QComboBox()
        self.duplicate_combo.addItems(["Ask me", "Skip", "Replace"])
        self.duplicate_combo.setFixedWidth(120)
        duplicate_section.addWidget(self.duplicate_combo)
        
        layout.addLayout(duplicate_section)
        
        layout.addStretch()
        
        # About
        about_label = QLabel(
            "YouTube Downloader Pro v1.0\n"
            "Built with PySide6 & yt-dlp\n\n"
            "Made by Cybertron\n"
            "Contact: ankit.cybertron@gmail.com"
        )
        about_label.setAlignment(Qt.AlignCenter)
        about_label.setStyleSheet("color: #8e8e93; font-size: 12px;")
        layout.addWidget(about_label)
        
        return tab
    
    def _apply_modern_theme(self):
        """Apply modern dark theme."""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # Dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(28, 28, 30))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(44, 44, 46))
        palette.setColor(QPalette.AlternateBase, QColor(58, 58, 60))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(58, 58, 60))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.Highlight, QColor(10, 132, 255))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
        app.setPalette(palette)
        
        # Stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1c1c1e;
            }
            
            QTabWidget::pane {
                border: none;
                background-color: #1c1c1e;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #8e8e93;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                border: none;
            }
            
            QTabBar::tab:selected {
                color: #ffffff;
                border-bottom: 2px solid #0a84ff;
            }
            
            QTabBar::tab:hover:!selected {
                color: #ffffff;
            }
            
            QTextEdit {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                color: #ffffff;
            }
            
            QTextEdit:focus {
                border: 1px solid #0a84ff;
            }
            
            QLineEdit {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #ffffff;
            }
            
            QPushButton {
                background-color: #2c2c2e;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                color: #ffffff;
            }
            
            QPushButton:hover {
                background-color: #3a3a3c;
            }
            
            QPushButton:pressed {
                background-color: #48484a;
            }
            
            QPushButton:disabled {
                background-color: #2c2c2e;
                color: #636366;
            }
            
            QPushButton:checked {
                background-color: #0a84ff;
            }
            
            QPushButton#downloadBtn {
                background-color: #0a84ff;
                font-size: 15px;
                font-weight: 600;
            }
            
            QPushButton#downloadBtn:hover {
                background-color: #0077ed;
            }
            
            QComboBox {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #ffffff;
            }
            
            QComboBox:disabled {
                color: #636366;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2c2c2e;
                selection-background-color: #0a84ff;
                border-radius: 8px;
            }
            
            QSpinBox {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                color: #ffffff;
            }
            
            QListWidget {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 10px;
                padding: 8px;
                font-size: 13px;
            }
            
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px 0;
            }
            
            QListWidget::item:selected {
                background-color: #0a84ff;
            }
            
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            
            QProgressBar {
                background-color: #3a3a3c;
                border: none;
                border-radius: 2px;
            }
            
            QProgressBar::chunk {
                background-color: #0a84ff;
                border-radius: 2px;
            }
            
            #downloadCard {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 12px;
            }
        """)
        
        # Set download button ID
        self.download_btn.setObjectName("downloadBtn")
    
    # Event handlers
    @Slot()
    def _on_browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_dir)
        if folder:
            self.output_dir = folder
            self.folder_input.setText(folder)
            self.manager.set_output_dir(folder)
    
    @Slot()
    def _on_start(self):
        """Start downloads with smart URL extraction."""
        text = self.url_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Input", "Please paste some text containing YouTube URLs.")
            return
        
        # Smart URL extraction - finds all YouTube URLs in any text
        urls = extract_youtube_urls(text)
        
        if not urls:
            QMessageBox.warning(
                self, 
                "No URLs Found", 
                "No YouTube URLs detected in the text.\n\n"
                "Supported formats:\n"
                "• youtube.com/watch?v=...\n"
                "• youtu.be/...\n"
                "• Playlists, Channels, Shorts"
            )
            return
        
        mode = DownloadMode.VIDEO if self.video_btn.isChecked() else DownloadMode.AUDIO
        quality = self.quality_combo.currentText().lower()
        speed_limit = self.speed_spin.value()
        workers = self.workers_spin.value()
        
        # Get format based on mode
        if mode == DownloadMode.AUDIO:
            output_format = self.audio_format_combo.currentText().lower()
        else:
            output_format = self.video_format_combo.currentText().lower()
        
        # Set duplicate handling policy
        dup_policy_text = self.duplicate_combo.currentText().lower()
        if "skip" in dup_policy_text:
            self.manager.set_duplicate_policy("skip")
        elif "replace" in dup_policy_text:
            self.manager.set_duplicate_policy("replace")
        else:
            self.manager.set_duplicate_policy("ask")
        
        self.manager.set_worker_count(workers)
        self.manager.set_output_dir(self.output_dir)
        
        for url in urls:
            self.manager.add_url(url, mode, quality, speed_limit, output_format)
        
        self.manager.start()
        
        # Switch to queue tab
        self.tabs.setCurrentIndex(1)
        self.url_input.clear()
        self.url_count_label.setText("")
        self._log(f"Detected and added {len(urls)} URL(s)")
    
    @Slot()
    def _on_pause(self):
        self.manager.pause()
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)
    
    @Slot()
    def _on_resume(self):
        self.manager.resume()
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
    
    @Slot()
    def _on_clear(self):
        for card in list(self.download_cards.values()):
            self.queue_layout.removeWidget(card)
            card.deleteLater()
        self.download_cards.clear()
        self.empty_label.show()
    
    @Slot()
    def _refresh_history(self):
        self.history_list.clear()
        history = self.manager.get_history()
        
        for entry in history:
            title = entry.get('title', 'Unknown')
            mode = entry.get('mode', 'audio').upper()
            ts = entry.get('timestamp', '')[:16].replace('T', ' ')
            
            item = QListWidgetItem(f"{title}\n{mode} • {ts}")
            self.history_list.addItem(item)
    
    # Signal handlers
    @Slot(str, str)
    def _on_download_started(self, item_id: str, title: str):
        self.empty_label.hide()
        card = DownloadCard(item_id, title)
        self.download_cards[item_id] = card
        self.queue_layout.insertWidget(self.queue_layout.count() - 1, card)
    
    @Slot(str, float, str)
    def _on_progress_updated(self, item_id: str, progress: float, status: str):
        if item_id in self.download_cards:
            self.download_cards[item_id].update_progress(progress, status)
    
    @Slot(str, str, str)
    def _on_download_completed(self, item_id: str, title: str, output_path: str):
        if item_id in self.download_cards:
            self.download_cards[item_id].set_completed()
        self._refresh_history()
    
    @Slot(str, str, str)
    def _on_download_failed(self, item_id: str, title: str, error: str):
        if item_id in self.download_cards:
            self.download_cards[item_id].set_failed(error)
    
    @Slot(str, str)
    def _on_download_skipped(self, item_id: str, reason: str):
        """Handle skipped download (file already exists)."""
        self._log(f"Skipped: {reason}")
    
    @Slot(str)
    def _on_log_message(self, msg: str):
        self._log(msg)
    
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{ts}] {msg}")
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    def closeEvent(self, event):
        self.manager.stop()
        event.accept()


def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Downloader Pro")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
