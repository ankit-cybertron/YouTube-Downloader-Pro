"""
worker.py - Download Engine for YouTube Downloader Pro

This module provides:
- Thread-safe download queue management
- QThread-based worker system for parallel downloads
- yt-dlp integration with progress hooks
- Pause/Resume functionality
- Failed download tracking and auto-retry
- Download history management
- Metadata fetching without downloading
"""

import os
import json
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
import threading

from PySide6.QtCore import QThread, Signal, QObject, QMutex, QWaitCondition, QRunnable, QThreadPool
import yt_dlp


class DownloadMode(Enum):
    """Download mode enum."""
    AUDIO = "audio"
    VIDEO = "video"


class DownloadStatus(Enum):
    """Download status enum."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class DownloadItem:
    """Represents a single download task."""
    url: str
    mode: DownloadMode
    quality: str = "best"
    output_dir: str = "./downloads"
    speed_limit: int = 0  # KB/s, 0 = unlimited
    output_format: str = "mp3"  # Audio: mp3/aac/wav/flac, Video: mp4/mkv/webm
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    title: str = ""
    thumbnail: str = ""  # Thumbnail URL
    error_message: str = ""
    output_path: str = ""
    item_id: str = field(default_factory=lambda: "")
    
    def __post_init__(self):
        if not self.item_id:
            self.item_id = f"{hash(self.url + str(datetime.now().timestamp()))}"


class DownloadSignals(QObject):
    """Signals for download worker communication."""
    progress_updated = Signal(str, float, str)  # item_id, progress, status_text
    download_started = Signal(str, str, str)  # item_id, title, thumbnail_url
    download_completed = Signal(str, str, str)  # item_id, title, output_path
    download_failed = Signal(str, str, str)  # item_id, title, error
    download_skipped = Signal(str, str)  # item_id, reason
    log_message = Signal(str)  # message
    queue_empty = Signal()
    all_workers_idle = Signal()


class MetadataSignals(QObject):
    """Signals for metadata fetching."""
    finished = Signal(dict)
    error = Signal(str)


class MetadataWorker(QRunnable):
    """Worker to fetch video metadata without downloading."""
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals = MetadataSignals()
        self.setAutoDelete(True)
        
    def run(self):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, # Need full info
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info:
                    self.signals.finished.emit(info)
                else:
                    self.signals.error.emit("Could not extract info")
        except Exception as e:
            self.signals.error.emit(str(e))


class DownloadWorker(QThread):
    """Worker thread for processing downloads."""
    
    def __init__(self, worker_id: int, task_queue: Queue, signals: DownloadSignals,
                 pause_mutex: QMutex, pause_condition: QWaitCondition, 
                 duplicate_policy: str = "ask"):
        super().__init__()
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.signals = signals
        self.pause_mutex = pause_mutex
        self.pause_condition = pause_condition
        self.duplicate_policy = duplicate_policy
        self._stop_requested = False
        self._paused = False
        self._current_item: Optional[DownloadItem] = None
    
    def request_stop(self):
        """Request the worker to stop after current download."""
        self._stop_requested = True
    
    def set_paused(self, paused: bool):
        """Set pause state."""
        self._paused = paused
        if not paused:
            self.pause_condition.wakeAll()
    
    def run(self):
        """Main worker loop."""
        while not self._stop_requested:
            # Check for pause
            self.pause_mutex.lock()
            while self._paused and not self._stop_requested:
                self.pause_condition.wait(self.pause_mutex)
            self.pause_mutex.unlock()
            
            if self._stop_requested:
                break
            
            try:
                # Get next item from queue (non-blocking)
                try:
                    item = self.task_queue.get(timeout=0.5)
                except:
                    continue
                
                self._current_item = item
                self._process_download(item)
                self._current_item = None
                self.task_queue.task_done()
                
            except Exception as e:
                # self.signals.log_message.emit(f"[Worker {self.worker_id}] Error: {str(e)}")
                pass
    
    def _process_download(self, item: DownloadItem):
        """Process a single download item."""
        item.status = DownloadStatus.DOWNLOADING
        
        try:
            # Build yt-dlp options
            ydl_opts = self._build_ydl_options(item)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get title if not provided
                if not item.title:
                    info = ydl.extract_info(item.url, download=False)
                    if info:
                        item.title = info.get('title', 'Unknown')
                        item.thumbnail = info.get('thumbnail', '')
                
                self._download_single(item, ydl_opts)
            
            item.status = DownloadStatus.COMPLETED
            
        except Exception as e:
            item.status = DownloadStatus.FAILED
            item.error_message = str(e)
            self.signals.download_failed.emit(item.item_id, item.title or item.url, str(e))
            self.signals.log_message.emit(f"[Worker {self.worker_id}] Failed: {item.url} - {str(e)}")
    
    def _download_single(self, item: DownloadItem, ydl_opts: dict):
        """Download a single video/audio."""
        self.signals.download_started.emit(item.item_id, item.title or item.url, item.thumbnail or "")
        
        # Create progress hook for this item
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    progress = (downloaded / total) * 100
                    item.progress = progress
                    speed = d.get('speed', 0) or 0
                    speed_str = f"{speed / 1024:.1f} KB/s" if speed else "-- KB/s"
                    eta = d.get('eta', 0) or 0
                    eta_str = f"ETA: {eta}s" if eta else ""
                    status_text = f"{progress:.1f}% | {speed_str} {eta_str}"
                    self.signals.progress_updated.emit(item.item_id, progress, status_text)
            
            elif d['status'] == 'finished':
                item.progress = 100
                item.output_path = d.get('filename', '')
                self.signals.progress_updated.emit(item.item_id, 100, "Processing...")
        
        # Update options with progress hook
        opts = ydl_opts.copy()
        opts['progress_hooks'] = [progress_hook]
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([item.url])
            
            item.status = DownloadStatus.COMPLETED
            self.signals.download_completed.emit(item.item_id, item.title, item.output_path)
            self.signals.log_message.emit(f"[Worker {self.worker_id}] Completed: {item.title}")
            
            # Add to history
            self._add_to_history(item)
            
        except Exception as e:
            raise e
    
    def _build_ydl_options(self, item: DownloadItem) -> dict:
        """Build yt-dlp options based on download item settings."""
        output_template = os.path.join(item.output_dir, '%(title)s.%(ext)s')
        
        opts = {
            'outtmpl': output_template,
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': True,
            'no_color': True,
            'socket_timeout': 30,
            'retries': 10,
            'prefer_ffmpeg': True,
        }
        
        if item.mode == DownloadMode.AUDIO:
            audio_format = item.output_format.lower()
            codec_map = {'mp3': 'mp3', 'aac': 'aac', 'wav': 'wav', 'flac': 'flac'}
            codec = codec_map.get(audio_format, 'mp3')
            
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': codec, 'preferredquality': '192'},
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                ],
            })
        else:
            # Video
            container = item.output_format.lower() if item.output_format.lower() in ['mp4', 'mkv', 'webm'] else 'mp4'
            
            # Simplified format selection for robustness
            if item.quality == 'best':
                format_str = f"bestvideo+bestaudio/best"
            elif item.quality in ['1080p', '720p', '480p', '360p']:
                h = item.quality[:-1]
                format_str = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
            else:
                format_str = f"bestvideo+bestaudio/best"

            opts.update({
                'format': format_str,
                'merge_output_format': container,
                'postprocessors': [{'key': 'FFmpegMetadata', 'add_metadata': True}],
            })
        
        return opts
    
    def _add_to_history(self, item: DownloadItem):
        """Add completed download to history.json."""
        try:
            history_path = Path(item.output_dir) / 'history.json'
            history = []
            
            if history_path.exists():
                with open(history_path, 'r') as f:
                    history = json.load(f)
            
            entry = {
                'title': item.title,
                'url': item.url,
                'mode': item.mode.value,
                'quality': item.quality,
                'output_path': item.output_path,
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
            }
            
            history.insert(0, entry)
            history = history[:50]
            
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass


class DownloadManager(QObject):
    """Manages the download queue and worker threads."""
    
    def __init__(self, output_dir: str = "./downloads", max_workers: int = 3):
        super().__init__()
        self.output_dir = output_dir
        self.max_workers = max_workers
        
        self.signals = DownloadSignals()
        self.task_queue: Queue = Queue()
        self.workers: List[DownloadWorker] = []
        self.items: Dict[str, DownloadItem] = {}
        
        self.threadpool = QThreadPool()
        
        self._paused = False
        self._pause_mutex = QMutex()
        self._pause_condition = QWaitCondition()
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def fetch_metadata(self, url: str, on_success, on_error):
        """Fetch metadata for a URL asynchronously."""
        worker = MetadataWorker(url)
        worker.signals.finished.connect(on_success)
        worker.signals.error.connect(on_error)
        self.threadpool.start(worker)

    def set_output_dir(self, path: str):
        self.output_dir = path
        Path(path).mkdir(parents=True, exist_ok=True)
        
    def set_worker_count(self, count: int):
        self.max_workers = max(1, min(5, count))

    def add_download(self, url: str, mode: str, quality: str, output_format: str, title: str = ""):
        """Add a download task."""
        mode_enum = DownloadMode.VIDEO if mode == "video" else DownloadMode.AUDIO
        item = DownloadItem(
            url=url,
            mode=mode_enum,
            quality=quality,
            output_format=output_format,
            output_dir=self.output_dir,
            title=title
        )
        self.items[item.item_id] = item
        self.task_queue.put(item)
        
        # Start work
        self.start()
        return item.item_id

    def start(self):
        """Start the download workers."""
        # Clean up dead workers
        self.workers = [w for w in self.workers if w.isRunning()]
        
        while len(self.workers) < self.max_workers and not self.task_queue.empty():
            worker = DownloadWorker(
                worker_id=len(self.workers) + 1,
                task_queue=self.task_queue,
                signals=self.signals,
                pause_mutex=self._pause_mutex,
                pause_condition=self._pause_condition
            )
            worker.start()
            self.workers.append(worker)

    def get_history(self) -> List[Dict[str, Any]]:
        history_path = Path(self.output_dir) / 'history.json'
        if not history_path.exists():
            return []
        try:
            with open(history_path, 'r') as f:
                return json.load(f)
        except:
            return []

    def stop(self):
        for w in self.workers:
            w.request_stop()
        self.threadpool.clear()
