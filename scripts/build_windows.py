
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_windows():
    """Build script for Windows EXE using PyInstaller"""
    
    if sys.platform != "win32":
        print("❌ Error: This script must be run on Windows to generate an .exe file.")
        print("   Cross-compilation from macOS/Linux to Windows is not supported by PyInstaller.")
        return

    # Setup paths
    project_root = Path(__file__).parent.parent.absolute()
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
        
    print("🚀 Starting PyInstaller Build for Windows...")
    
    # Check for icon
    icon_path = project_root / "assets" / "icon.ico"
    if not icon_path.exists():
        # Fallback to png if ico doesn't exist, though ico is preferred for Windows
        icon_path = project_root / "assets" / "icon.png"
        if not icon_path.exists():
            print("⚠️ Warning: Icon not found")
        
    # PyInstaller Arguments
    cmd = [
        "pyinstaller",
        "--name", "YouTubeDownloaderPro",
        "--windowed",      # No console window
        "--onefile",       # Single .exe file!
        "--clean",
        "--noconfirm",
        
        # Icon
        f"--icon={str(icon_path)}",
        
        # Data (Windows uses semicolon separator)
        f"--add-data={project_root}/assets;assets",
        
        # Hidden Imports
        "--hidden-import", "PySide6",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "requests",
        
        # Optimizations
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        
        # Entry Point
        str(project_root / "src/desktop/main.py")
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd, cwd=project_root)
        print("\n✅ Build complete!")
        print(f"📂 EXE located at: {dist_dir}\\YouTubeDownloaderPro.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        input("Press Enter to exit...") # Keep window open on error

if __name__ == "__main__":
    build_windows()
