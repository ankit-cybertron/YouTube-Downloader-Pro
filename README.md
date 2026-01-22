# YouTube Downloader Pro

<p align="center">
  <img src="icon.png" width="150" alt="YouTube Downloader Pro Icon">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-6.8.x-green.svg" alt="PySide6">
  <img src="https://img.shields.io/badge/yt--dlp-Latest-red.svg" alt="yt-dlp">
  <img src="https://img.shields.io/badge/Platform-macOS-lightgrey.svg" alt="Platform">
</p>

A modern, minimal, and powerful desktop application for downloading YouTube content. Built with **PySide6** and **yt-dlp**, featuring a clean dark-mode interface, smart smart URL detection, and queue management.

---

## 📖 About

YouTube Downloader Pro is designed to be the ultimate tool for archiving your favorite content. Whether you need a high-quality video for offline viewing or an MP3 audio track for your playlist, this tool handles it with style and speed.

### Key Features

*   **Smart URL Detection**: Automatically finds YouTube links in any pasted text (playlists, channels, shorts, etc.).
*   **Format Selection**: Choose between **MP3, AAC, WAV, FLAC** for audio and **MP4, MKV, WEBM** for video.
*   **Quality Control**: Select video resolution from 360p up to Best available.
*   **Queue Management**: Pause, resume, and manage multiple downloads simultaneously.
*   **Duplicate Detection**: Intelligent checking for existing files with Skip/Replace options.
*   **Modern UI**: Sleek dark mode interface with native macOS feel.

---

## ✨ Features Breakdown

### 🎯 Smart Link Detection
Paste a paragraph, a message, or a list of links. The app automatically extracts:
*   Standard videos (`youtube.com/watch?v=...`)
*   Short links (`youtu.be/...`)
*   Playlists (`youtube.com/playlist?list=...`)
*   Channel URLs (`youtube.com/@channel`)

### ⚡ Parallel Downloads
Download multiple files at once. The multi-threaded worker system ensures your UI stays responsive while heavy lifting happens in the background.

### 🛡️ Duplicate Handling
Never accidentally overwrite your files.
*   **Ask me**: Decide on a case-by-case basis.
*   **Skip**: Automatically skip files that already exist.
*   **Replace**: Force re-download and replace existing files.

---

## 🛠 Installation & Usage

### Running from Source

1.  **Clone the repository**
    ```bash
    git clone https://github.com/ankit-cybertron/yt-downloader-pro.git
    cd yt-downloader-pro
    ```

2.  **Set up environment**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run the app**
    ```bash
    python app.py
    ```

### Building the App (macOS)

To create a standalone `.app` file:

```bash
# Install PyInstaller
pip install pyinstaller pillow

# Build
pyinstaller --name "YouTube Downloader Pro" --windowed --onefile --icon=icon.png app.py
```

The app will be available in the `dist/` folder.

---

## ⚙️ Configuration

The **Settings** tab allows you to configure:
*   **Output Folder**: Where your downloads are saved.
*   **Parallel Downloads**: Number of simultaneous downloads (1-5).
*   **Speed Limit**: Cap download speed if needed.
*   **Duplicate Policy**: Set your default preference for handling existing files.

---

## 👤 Author

**Ankit Kumar Tiwari**
*   **Contact**: ankit.cybertron@gmail.com
*   **GitHub**: [ankit-cybertron](https://github.com/ankit-cybertron)

---

<p align="center">
  <i>Made with ❤️ by Cybertron</i>
</p>
