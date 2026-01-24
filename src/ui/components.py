from typing import List
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, 
    QDialog, QListWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

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
