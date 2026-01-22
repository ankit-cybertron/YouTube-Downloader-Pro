# YouTube Downloader Pro

A production-grade macOS desktop application for downloading YouTube content, built with Python, PySide6 (Qt 6), and yt-dlp.

![macOS](https://img.shields.io/badge/macOS-Compatible-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

### Core Functionality
- **Audio Downloads**: Best quality audio converted to MP3 with embedded metadata and thumbnail
- **Video Downloads**: Multiple quality options (Best, 1080p, 720p, 480p, 360p)
- **Playlist & Channel Support**: Automatically expands and downloads all entries
- **Shorts Support**: Works with YouTube Shorts

### Download Management
- **Parallel Downloads**: Configure 1-5 simultaneous workers
- **Pause/Resume**: Queue-safe pause that allows active downloads to complete
- **Speed Limiting**: User-configurable download speed limit (KB/s)
- **Auto-Retry**: Failed downloads are automatically retried on next launch

### User Interface
- **Native macOS Look**: Qt Fusion dark theme optimized for macOS
- **Real-time Progress**: Per-download progress bars with speed and ETA
- **Log Output**: Live status messages and error reporting
- **Download History**: View last 50 completed downloads

## Requirements

### System Requirements
- macOS 10.15 (Catalina) or later
- Python 3.10 or later
- FFmpeg (for audio conversion and video merging)

### Installing FFmpeg

Using Homebrew:
```bash
brew install ffmpeg
```

Or download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Installation

### 1. Clone or Download
```bash
cd /path/to/your/projects
# Clone or copy the yt-downloader-pro folder
```

### 2. Create Virtual Environment (Recommended)
```bash
cd yt-downloader-pro
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode
```bash
cd yt-downloader-pro
source venv/bin/activate  # If using virtual environment
python app.py
```

## Building macOS App Bundle

### Using PyInstaller

1. **Install PyInstaller** (included in requirements.txt):
```bash
pip install pyinstaller
```

2. **Build the .app bundle**:
```bash
pyinstaller --name "YouTube Downloader Pro" \
            --windowed \
            --onefile \
            --icon=icon.icns \
            --add-data "downloads:downloads" \
            app.py
```

3. **Find the built app**:
```bash
open dist/
# Double-click "YouTube Downloader Pro.app" to run
```

### Optional: Add Custom Icon
1. Create or download a 1024x1024 PNG icon
2. Convert to .icns format:
```bash
# Using iconutil (built-in to macOS)
mkdir icon.iconset
sips -z 16 16 icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32 icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32 icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64 icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256 icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256 icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512 icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512 icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset
```

## Usage Guide

### Basic Download
1. Paste one or more YouTube URLs (one per line)
2. Select **Audio (MP3)** or **Video** mode
3. If Video mode, select quality from dropdown
4. Click **Start Download**

### Supported URL Types
- Single videos: `https://www.youtube.com/watch?v=...`
- Playlists: `https://www.youtube.com/playlist?list=...`
- Channels: `https://www.youtube.com/@channelname`
- Shorts: `https://www.youtube.com/shorts/...`

### Settings
| Setting | Description |
|---------|-------------|
| **Mode** | Audio (MP3) or Video |
| **Quality** | Video resolution (only for Video mode) |
| **Speed Limit** | Max download speed in KB/s (0 = unlimited) |
| **Parallel Downloads** | Number of simultaneous downloads (1-5) |
| **Output Folder** | Destination for downloaded files |

### Pause/Resume Behavior
- **Pause**: Stops dispatching new downloads; active downloads finish
- **Resume**: Continues the queue; partial files are resumed using yt-dlp's continuedl feature

## Project Structure

```
yt-downloader-pro/
├── app.py              # Main GUI application (PySide6)
├── worker.py           # Download engine (queue, workers, yt-dlp)
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── downloads/          # Default output directory
├── history.json        # Download history (auto-created)
├── failed.txt          # Failed downloads for retry (auto-created)
└── icon.icns           # macOS app icon (optional)
```

## Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Install FFmpeg: `brew install ffmpeg`
- Or specify path in worker.py: `'ffmpeg_location': '/path/to/ffmpeg'`

**"Download failed" errors**
- Check internet connection
- Some videos may be geo-restricted or private
- Age-restricted videos may require cookies

**App not opening after build**
- Right-click → Open (first time only, bypasses Gatekeeper)
- Or: `xattr -cr "dist/YouTube Downloader Pro.app"`

**Slow downloads**
- Increase parallel workers (up to 5)
- Remove speed limit (set to 0)
- YouTube may throttle downloads

### Debug Mode
To see detailed yt-dlp output, modify `worker.py`:
```python
# Change these options:
'quiet': False,
'verbose': True,
```

## Known Limitations

1. **Pause behavior**: Pause only stops new downloads; active downloads complete
2. **Age-restricted content**: May require browser cookies for authentication
3. **Live streams**: Not supported (VODs after stream ends work fine)
4. **Private videos**: Cannot download private or members-only content
5. **Rate limiting**: YouTube may temporarily limit frequent requests

## License

MIT License - Feel free to modify and distribute.

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube download library
- [PySide6](https://doc.qt.io/qtforpython-6/) - Qt for Python
- [FFmpeg](https://ffmpeg.org/) - Media processing
