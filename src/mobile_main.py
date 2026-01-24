
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.ui.mobile_window import MobileWindow

def main():
    # Note: Qt6 handles high DPI scaling automatically, no need for AA_EnableHighDpiScaling
    app = QApplication(sys.argv)
    app.setApplicationName("YT Downloader Pro")
    
    # On Android, windows utilize the full screen automatically
    window = MobileWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
