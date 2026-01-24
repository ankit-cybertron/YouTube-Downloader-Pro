#!/usr/bin/env python3
"""
Run Mobile Application (for testing on desktop)
Usage: python run_mobile.py

This runs the mobile UI in a phone-sized window for testing.
To build the actual APK, use: python scripts/build_android.py
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
    
    # Run the mobile app
    mobile_main = os.path.join(project_root, "src", "mobile", "main.py")
    
    if os.path.exists(mobile_main):
        subprocess.run([python_exe, mobile_main], cwd=project_root)
    else:
        # Fallback to old structure
        old_main = os.path.join(project_root, "src", "mobile_main.py")
        subprocess.run([python_exe, old_main], cwd=project_root)


if __name__ == "__main__":
    main()
