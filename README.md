# YouTube Downloader Pro

A professional, minimal, and smart YouTube Downloader for desktop. Built with Python, PySide6, and the powerful `yt-dlp` engine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-v2.1.0-purple)

## ✨ Unique Features

### 🧠 Smart Recognition
Stop formatting your links manually! Paste **any text**—a paragraph, a chat log, or a list—and the app will intelligently:
*   Extract all YouTube video links.
*   Detect Playlists and Channels.
*   Count the results and offer a **Batch Download**.

### ℹ️ Info-First Workflow
We don't shoot in the dark. The app fetches video details (Title, Thumbnail, Duration) **before** asking you to download, ensuring you get the right content every time.

### 🔄 Built-in Updater
Stay current with a single click. The new **Check for Updates** feature in Settings connects directly to GitHub Releases.

## 🚀 Installation

### Option A: Standalone Executable (Recommended)
Download the latest release for your OS from the [Releases Page](https://github.com/ankit-cybertron/YouTube-Downloader-Pro/releases).
*   **Windows**: Run the `.exe` file directly.
*   **macOS**: Open the `.app` bundle.

### Option B: Run from Source

**Prerequisites:** Python 3.10+ and [FFmpeg](https://ffmpeg.org/download.html).

```bash
# Clone
git clone https://github.com/ankit-cybertron/YouTube-Downloader-Pro.git
cd YouTube-Downloader-Pro

# Setup Environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install
pip install -r requirements.txt

# Run
python run_desktop.py
```

## 📦 Building Your Own

Create standalone executables for distribution.

**Windows (.exe)**
```powershell
# Run on a Windows machine
python scripts/build_windows.py
```

**macOS (.app)**
```bash
# Run on a Mac
python scripts/build_macos.py
```

## 🛠 Project Structure

```
yt-downloader-pro/
├── src/
│   ├── desktop/         # Main GUI Application
│   ├── core/            # Download Engine & Workers
│   └── ui/              # Shared Components
├── scripts/             # Build scripts (PyInstaller)
├── archive/             # Legacy/Mobile code
└── dist/                # Output directory for builds
```

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
**Disclaimer**: This tool is for personal and educational use. Respect creator copyrights and YouTube's Terms of Service.
