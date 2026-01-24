#!/usr/bin/env python3
"""
Build script for macOS App Bundle (Mobile Version) using PyInstaller
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_mobile_app():
    # Build directory setup
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
        
    print("🚀 Starting PyInstaller Build for Mobile App...")
        
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", "YT Downloader Pro Mobile",
        "--windowed",
        "--onedir",
        "--clean",
        "--noconfirm",
        
        # Icon
        "--icon", str(project_root / "assets/icon.png"),
        
        # Data files
        f"--add-data={project_root}/assets:assets",
        
        # Hidden imports (critical for yt-dlp and pyside6)
        "--hidden-import", "PySide6",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "yt_dlp.extractor.youtube",
        "--hidden-import", "yt_dlp.extractor.common",
        
        # Optimization: Exclude heavy unnecessary modules if possible
        # but be careful with yt-dlp as it lazy loads everything
        "--collect-all", "yt_dlp", 
        
        # Main entry point
        str(project_root / "src/mobile/main.py")
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=project_root)
    
    print("\n✅ Build complete!")
    print(f"📂 App is located at: {dist_dir}/YT Downloader Pro Mobile.app")

if __name__ == "__main__":
    build_mobile_app()
