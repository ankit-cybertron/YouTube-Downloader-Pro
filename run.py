
#!/usr/bin/env python3
"""
Launcher script that automatically sets up the environment and runs the app.
"""
import sys
import os
import subprocess
from pathlib import Path

def main():
    # project root is where this script is located
    project_root = Path(__file__).parent.absolute()
    
    # Virtual env path
    venv_path = project_root / "venv"
    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        python_executable = venv_path / "bin" / "python"

    # If we are not currently running via the venv python, and the venv exists, restart using it
    if venv_path.exists():
        # Compare absolute paths to handle symlinks resolution etc.
        current_exe = Path(sys.executable).resolve()
        target_exe = python_executable.resolve()
        
        if current_exe != target_exe:
            print(f"🔄 Switching to virtual environment: {target_exe}")
            # Re-execute this script with the venv python
            try:
                subprocess.run([str(target_exe), str(project_root / "run.py")] + sys.argv[1:], check=True)
                return
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)
            except FileNotFoundError:
                print(f"❌ Error: Python executable not found at {target_exe}")
                print("   Please ensure virtual environment is created correctly.")
                sys.exit(1)
    
    # If we are here, we are either in the venv OR venv doesn't exist (fallback to system python)
    # Add project root to path
    sys.path.insert(0, str(project_root))
    
    try:
        from src.main import main as app_main
        app_main()
    except ModuleNotFoundError as e:
        print(f"❌ Error: Missing dependency - {e}")
        print("   Have you installed requirements? Try: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
