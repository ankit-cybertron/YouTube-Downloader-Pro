
#!/usr/bin/env python3
"""
Build script for macOS App Bundle
"""
import os
import shutil
import subprocess
from pathlib import Path

def build_app():
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
        
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", "YouTube Downloader Pro",
        "--windowed",
        "--onedir",  # Use onedir for proper app bundle on macOS
        "--icon=assets/icon.png",
        "--add-data", "assets/icon.png:assets",  # Include icon in bundle
        "--noconfirm",
        "--clean",
        "src/main.py"
    ]
    
    print(f"Running build command: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    print("\nBuild complete! App is located at 'dist/YouTube Downloader Pro.app'")

if __name__ == "__main__":
    build_app()
