# Release v2.1.0: The Desktop Pro Update 🚀

This is a major release that completely redesigns the desktop experience with a modern, professional UI and smart features.

## ✨ New Features

*   **New Professional UI**: A clean, light-themed interface with a split-view design for download details.
*   **Smart Link Detection**: Paste paragraphs of text, and the app will automatically detect and count all YouTube links.
*   **Info-First Workflow**: Fetches video metadata (Title, Duration, Thumbnail) *before* you download, so you know exactly what you're getting.
*   **Batch & Playlist Support**: Automatically detects playlists or multiple links and offers to queue them all at once.
*   **Update Checker**: Built-in "Check for Updates" button in Settings to notify you of new releases.
*   **Sidebar Navigation**: Easy access to Queue, History, and Settings.

## 🛠 Improvements

*   **Performance**: Optimized worker threads for smoother UI during metadata fetching.
*   **Native Builds**: Improved build scripts for generating standalone macOS `.app` and Windows `.exe` files.
*   **Format Selection**: Simplified choices for standard quality levels (1080p, 720p, Audio MP3).

## 📦 Download

### Windows
*   **YouTubeDownloaderPro.exe**: Single portable executable. No installation required.

### macOS
*   **YouTube Downloader Pro.app**: Native macOS application bundle.

---

### How to Build from Source

If you prefer running from source:

```bash
git clone https://github.com/ankit-cybertron/YouTube-Downloader-Pro.git
cd YouTube-Downloader-Pro
pip install -r requirements.txt
python run_desktop.py
```
