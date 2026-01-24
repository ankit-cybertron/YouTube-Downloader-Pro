#!/usr/bin/env python3
"""
Build script for YouTube Downloader Pro (Desktop) - macOS
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_app():
    # Setup paths
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
        
    print("🚀 Starting PyInstaller Build for Desktop App...")
    
    # Check for icon
    icon_path = project_root / "assets" / "icon.png"
    if not icon_path.exists():
        print("⚠️ Warning: Icon not found at assets/icon.png")
        
    # PyInstaller Arguments
    cmd = [
        "pyinstaller",
        "--name", "YouTube Downloader Pro",
        "--windowed",  # No terminal
        "--onedir",    # Folder bundle (faster start than onddfile)
        "--clean",
        "--noconfirm",
        
        # Icon
        "--icon", str(icon_path),
        
        # Data
        f"--add-data={project_root}/assets:assets",
        
        # Hidden Imports (Critical)
        "--hidden-import", "PySide6",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "yt_dlp.extractor.youtube",
        "--hidden-import", "yt_dlp.extractor.common",
        "--hidden-import", "requests",
        
        # Collect all of yt_dlp to be safe
        "--collect-all", "yt_dlp",
        
        # Optimization: Exclude unnecessary heavy modules
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "PySide6.QtQuick",
        "--exclude-module", "PySide6.QtQml",
        "--exclude-module", "PySide6.Qt3DCore",
        "--exclude-module", "PySide6.QtWebEngineCore",
        "--exclude-module", "PySide6.QtWebSockets",
        "--exclude-module", "PySide6.QtMultimedia",
        "--exclude-module", "PySide6.QtCharts",
        "--exclude-module", "PySide6.QtDataVisualization",
        "--exclude-module", "PySide6.QtSensors",
        "--exclude-module", "PySide6.QtTest",
        
        # Entry Point
        str(project_root / "src/desktop/main.py")
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd, cwd=project_root)
        print("\n✅ Build complete!")
        print(f"📂 App located at: {dist_dir}/YouTube Downloader Pro.app")
        print("To run: open 'dist/YouTube Downloader Pro.app'")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_app()
