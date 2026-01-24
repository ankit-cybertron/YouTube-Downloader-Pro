# YouTube Downloader Pro

<div align="center">

![YT Downloader Pro](assets/icon.png)

**A powerful, cross-platform YouTube downloader with desktop and mobile versions**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)](https://doc.qt.io/qtforpython-6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ✨ Features

- 🎵 **Audio Downloads** - MP3, AAC, WAV, FLAC formats
- 🎬 **Video Downloads** - MP4, MKV, WEBM formats with quality selection
- 📥 **Smart URL Detection** - Paste any text and URLs are auto-detected
- 📋 **Clipboard Integration** - Auto-detects YouTube URLs from clipboard
- ⏬ **Parallel Downloads** - Download up to 5 files simultaneously
- 📊 **Live Progress** - Real-time progress bars with speed and ETA
- 🖼️ **Thumbnails** - Shows video thumbnails during download
- 📜 **Download History** - Track all your past downloads
- ⚙️ **Customizable** - Speed limits, output folder, duplicate handling
- 🌙 **Dark Theme** - Beautiful modern dark UI

## 📱 Platforms

| Platform | Status | Entry Point |
|----------|--------|-------------|
| Desktop (macOS/Windows/Linux) | ✅ Ready | `python run_desktop.py` |
| Mobile (Android APK) | ✅ Ready | `python scripts/build_android.py` |

---

## 📁 Project Structure

```
yt-downloader-pro/
├── src/
│   ├── core/                   # Shared business logic
│   │   ├── __init__.py
│   │   ├── worker.py           # Download engine (yt-dlp)
│   │   └── utils.py            # URL extraction, utilities
│   │
│   ├── desktop/                # Desktop application
│   │   ├── __init__.py
│   │   ├── main.py             # Desktop entry point
│   │   └── ui/
│   │       ├── __init__.py
│   │       ├── main_window.py  # Desktop UI
│   │       └── components.py   # Reusable widgets
│   │
│   └── mobile/                 # Mobile application
│       ├── __init__.py
│       ├── main.py             # Mobile/Android entry point
│       └── ui/
│           ├── __init__.py
│           └── mobile_window.py # Mobile UI (Carbon & Crimson theme)
│
├── scripts/
│   ├── build_macos.py          # Build macOS .app bundle
│   └── build_android.py        # Build Android APK
│
├── android/                    # Android configuration
│   ├── AndroidManifest.xml
│   └── res/
│       └── xml/
│           └── file_paths.xml
│
├── assets/
│   └── icon.png                # App icon
│
├── downloads/                  # Default output directory
│
├── run_desktop.py              # Quick launcher for desktop
├── run_mobile.py               # Quick launcher for mobile testing
├── requirements.txt            # Python dependencies
├── pysidedeploy.spec           # Android APK config
├── ANDROID_BUILD.md            # Android build instructions
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/cybertron/yt-downloader-pro.git
cd yt-downloader-pro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
# Desktop version
python run_desktop.py

# Mobile version (for testing on desktop)
python run_mobile.py
```

---

## 📱 Building Android APK

### Prerequisites for Android Build

1. **Java JDK 17+**
   ```bash
   # macOS
   brew install openjdk@17
   export JAVA_HOME=/opt/homebrew/opt/openjdk@17
   ```

2. **Android SDK**
   ```bash
   # Set environment variable
   export ANDROID_SDK_ROOT=$HOME/Android
   
   # Install required packages
   sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
   ```

### Build APK

```bash
# Check environment and build
python scripts/build_android.py

# Check only (no build)
python scripts/build_android.py --check-only

# Build release APK
python scripts/build_android.py --release
```

For detailed instructions, see [ANDROID_BUILD.md](ANDROID_BUILD.md).

---

## 💻 Building Desktop App

### macOS Bundle

```bash
python scripts/build_macos.py
```

The `.app` bundle will be created in `dist/`.

### Windows/Linux

```bash
pip install pyinstaller
pyinstaller --onefile --windowed src/desktop/main.py
```

---

## 🎨 Mobile UI Theme

The mobile version features a stunning **"Carbon & Crimson"** dark theme:

- **Background**: Deep charcoal (#0A0A0A)
- **Surface**: Rich black (#161616)
- **Accent**: Neon red (#FF3131)
- **Typography**: Clean sans-serif

Features:
- Bottom navigation bar (iOS-style)
- Auto-paste from clipboard
- Video thumbnails in download list
- Glassmorphism card effects
- Smooth animations

---

## 📋 Requirements

```
PySide6>=6.6.0
yt-dlp>=2024.1.0
```

---

## 🔧 Configuration

### Settings Tab Options

| Setting | Description | Default |
|---------|-------------|---------|
| Output Folder | Where to save downloads | `./downloads` |
| Parallel Downloads | Simultaneous downloads | 3 |
| Speed Limit | Bandwidth limit (KB/s) | Unlimited |
| If File Exists | How to handle duplicates | Ask |

---

## 📝 Supported Platforms

- YouTube Videos (`youtube.com/watch?v=...`)
- YouTube Shorts (`youtube.com/shorts/...`)
- YouTube Playlists (`youtube.com/playlist?list=...`)
- YouTube Channels (`youtube.com/@channel`)
- Shortened URLs (`youtu.be/...`)

---

## 🐛 Troubleshooting

### "No JavaScript runtime found"
This is a yt-dlp warning. Install deno:
```bash
brew install deno  # macOS
# or
curl -fsSL https://deno.land/install.sh | sh
```

### Downloads are slow
Check your speed limit setting, and try reducing parallel downloads.

### APK build fails
Make sure JAVA_HOME and ANDROID_SDK_ROOT are set correctly.
See [ANDROID_BUILD.md](ANDROID_BUILD.md) for details.

---

## 👨‍💻 Author

**Cybertron (Ankit Agrawal)**

- Email: ankit.cybertron@gmail.com
- GitHub: [@cybertron](https://github.com/cybertron)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ by Cybertron**

</div>
