# YouTube Downloader Pro

A professional, minimal, and smart YouTube Downloader for desktop. Built with Python, PySide6, and the powerful `yt-dlp` engine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

*   **Smart Recognition**: Paste text paragraphs containing multiple links, playlists, or channels—the app auto-detects everything.
*   **Professional UI**: Clean, light theme optimized for readability and ease of use.
*   **Info-First Workflow**: Fetches video metadata (Title, Thumbnail, Duration) *before* you download.
*   **Format Control**: Choose between Video (1080p, 720p, 480p) or Audio (MP3, Best Quality).
*   **Batch Downloading**: Queue management with concurrent downloads.
*   **History Tracking**: Keep a log of your downloaded content.

## 🚀 Installation & Running

### Prerequisites
*   Python 3.10 or higher.
*   [FFmpeg](https://ffmpeg.org/download.html) (Installed and added to PATH).

### Setup (Mac/Linux)

```bash
# Clone the repository
git clone https://github.com/ankit-cybertron/YouTube-Downloader-Pro.git
cd YouTube-Downloader-Pro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python run_desktop.py
```

### Setup (Windows)

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python run_desktop.py
```

---

## 📦 Building Executables

You can create standalone applications (`.app` for macOS, `.exe` for Windows) so users don't need Python installed.

### Build on macOS
Generates a `YouTube Downloader Pro.app` bundle.

```bash
source venv/bin/activate
python scripts/build_macos.py
```
> Output located in `dist/`

### Build on Windows
Generates a single `YouTubeDownloaderPro.exe` file.

```powershell
.\venv\Scripts\activate
python scripts/build_windows.py
```
> Output located in `dist/`

---

## 🛠 Project Structure

```
yt-downloader-pro/
├── src/
│   ├── desktop/
│   │   ├── main.py          # Entry point
│   │   └── ui/              # UI definitions (PySide6)
│   └── core/
│       ├── worker.py        # Download threads & logic
│       └── utils.py         # Helpers (Regex, etc)
├── scripts/                 # Build scripts
├── assets/                  # Icons and resources
└── archive/                 # Old mobile/android v1 code
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
**Note**: This application is for educational purposes. Please respect YouTube's Terms of Service and copyright laws.
