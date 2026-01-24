#!/usr/bin/env python3
"""
YouTube Downloader Pro - Desktop Application Entry Point
Run this to launch the desktop version on macOS/Windows/Linux
"""

import sys
import os

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.desktop.ui.main_window import MainWindow
from src.core.utils import resource_path


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Downloader Pro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Cybertron")
    
    # Set app icon
    icon_path = resource_path("assets/icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
