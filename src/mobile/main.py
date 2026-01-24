#!/usr/bin/env python3
"""
YouTube Downloader Pro - Mobile Application Entry Point
This is the entry point for Android APK builds

Run locally: python -m src.mobile.main
Build APK:   python scripts/build_android.py
"""

import sys
import os

# Ensure project root is in path for both local and APK execution
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QGuiApplication

from src.mobile.ui.mobile_window import MobileWindow
from src.core.utils import resource_path


def main():
    # Qt6 handles high DPI scaling automatically
    app = QApplication(sys.argv)
    app.setApplicationName("YT Downloader Pro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Cybertron")
    
    # Set app icon
    icon_path = resource_path("assets/icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show mobile window
    window = MobileWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
