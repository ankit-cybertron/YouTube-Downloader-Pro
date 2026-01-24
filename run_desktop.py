#!/usr/bin/env python3
"""
Run Desktop Application
Usage: python run_desktop.py
"""

import os
import sys
import subprocess

def main():
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Activate virtual environment if it exists
    venv_python = os.path.join(project_root, "venv", "bin", "python")
    if os.path.exists(venv_python):
        python_exe = venv_python
    else:
        python_exe = sys.executable
    
    # Run the desktop app
    desktop_main = os.path.join(project_root, "src", "desktop", "main.py")
    
    if os.path.exists(desktop_main):
        subprocess.run([python_exe, desktop_main], cwd=project_root)
    else:
        # Fallback to old structure
        old_main = os.path.join(project_root, "src", "main.py")
        subprocess.run([python_exe, old_main], cwd=project_root)


if __name__ == "__main__":
    main()
