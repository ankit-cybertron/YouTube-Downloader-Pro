from typing import List
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, 
    QDialog, QListWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

# Use system font or simple sans-serif
import sys
# Use system font or simple sans-serif
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica Neue"

class DownloadCard(QFrame):
    """Minimalist progress card."""
    
    def __init__(self, item_id: str, title: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        
        # Styles
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 6px;
                border: 1px solid #3E3E42;
            }
            QLabel {
                border: none;
                color: #E0E0E0;
            }
        """)
        self.setFixedHeight(65)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Row 1: Title + Status
        top_row = QHBoxLayout()
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        top_row.addWidget(self.title_label, 1)
        
        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignRight)
        top_row.addWidget(self.status_label)
        
        layout.addLayout(top_row)
        
        # Row 2: Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333333;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #007ACC;
                border-radius: 2px;
            }
        """)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
    
    def update_progress(self, progress: float, status: str):
        self.progress_bar.setValue(int(progress))
        self.status_label.setText(status)
        
        # Reset style if coming back from error/done
        if progress < 100:
             self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background-color: #333333;
                    border-radius: 2px;
                    border: none;
                }
                QProgressBar::chunk {
                    background-color: #007ACC;
                    border-radius: 2px;
                }
            """)
    
    def set_completed(self):
        self.progress_bar.setValue(100)
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("color: #4EC9B0; font-size: 11px;")
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #333; border-radius: 2px; }
            QProgressBar::chunk { background-color: #4EC9B0; border-radius: 2px; }
        """)
    
    def set_failed(self, error: str):
        self.progress_bar.setValue(0)
        self.status_label.setText("Failed")
        self.status_label.setStyleSheet("color: #F44747; font-size: 11px;")
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #333; border-radius: 2px; }
            QProgressBar::chunk { background-color: #F44747; border-radius: 2px; }
        """)


class DuplicateDialog(QDialog):
    """Dialog for handling duplicate files."""
    
    SKIP = 0
    REPLACE = 1
    SKIP_ALL = 2
    REPLACE_ALL = 3
    
    def __init__(self, duplicates: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Conflict")
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: #EEE; }
            QLabel { color: #EEE; }
            QListWidget { background-color: #252526; border: 1px solid #3E3E42; color: #AAA; }
            QPushButton { 
                background-color: #333; color: white; border: 1px solid #444; 
                padding: 6px 12px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        
        self.result_action = self.SKIP
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel(f"{len(duplicates)} file(s) already exist:"))
        
        file_list = QListWidget()
        for d in duplicates[:5]:
            file_list.addItem(d)
        if len(duplicates) > 5:
            file_list.addItem("...")
        layout.addWidget(file_list)
        
        btn_layout = QHBoxLayout()
        btn_skip = QPushButton("Skip")
        btn_skip.clicked.connect(lambda: self._set_result(self.SKIP))
        
        btn_replace = QPushButton("Replace")
        btn_replace.clicked.connect(lambda: self._set_result(self.REPLACE))
        
        btn_layout.addWidget(btn_skip)
        btn_layout.addWidget(btn_replace)
        layout.addLayout(btn_layout)
        
    def _set_result(self, action):
        self.result_action = action
        self.accept()
