#!/usr/bin/env python3
"""
build_app.py - Build script for YouTube Downloader Pro

This script automates the process of building the standalone macOS application
using PyInstaller. It handles dependency checks, cleaning, and building.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_step(message):
    print(f"\n{'='*60}")
    print(f" {message}")
    print(f"{'='*60}\n")

def check_dependencies():
    """Check if required build tools are installed."""
    print_step("Checking Build Dependencies")
    
    required = ['pyinstaller', 'pillow']
    missing = []
    
    for pkg in required:
        try:
            subprocess.run([sys.executable, "-m", "pip", "show", pkg], 
                         check=True, capture_output=True)
            print(f"✅ {pkg} is installed")
        except subprocess.CalledProcessError:
            print(f"❌ {pkg} is missing")
            missing.append(pkg)
    
    if missing:
        print(f"\nInstalling missing dependencies: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("✅ Dependencies installed")

def clean_build():
    """Remove previous build artifacts."""
    print_step("Cleaning Previous Builds")
    
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['YouTube Downloader Pro.spec']
    
    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"Removing directory: {d}")
            shutil.rmtree(d)
            
    for f in files_to_clean:
        if os.path.exists(f):
            print(f"Removing file: {f}")
            os.remove(f)

def build_app():
    """Run PyInstaller to build the app."""
    print_step("Building Application")
    
    app_name = "YouTube Downloader Pro"
    main_script = "app.py"
    icon_file = "icon.png"
    
    # Check if icon exists
    if not os.path.exists(icon_file):
        print("⚠️ Warning: icon.png not found. Building without icon.")
        icon_arg = []
    else:
        print(f"Using icon: {icon_file}")
        icon_arg = [f"--icon={icon_file}"]
    
    # PyInstaller arguments
    args = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name", app_name,
        "--windowed",     # macOS .app bundle / no console
        "--onefile",      # Single executable
    ] + icon_arg + [main_script]
    
    print(f"Running command: {' '.join(args)}")
    
    try:
        subprocess.check_call(args)
        print("\n✅ Build Successful!")
        
        dist_path = os.path.abspath("dist")
        app_path = os.path.join(dist_path, f"{app_name}.app")
        
        print_step("Build Artifacts")
        print(f"App Bundle: {app_path}")
        print(f"Folder:     {dist_path}")
        print("\nTo run the app:")
        print(f"open '{app_path}'")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed with exit code {e.returncode}")
        sys.exit(1)

def main():
    # Ensure we are in the script's directory
    os.chdir(Path(__file__).parent)
    
    check_dependencies()
    clean_build()
    build_app()

if __name__ == "__main__":
    main()
