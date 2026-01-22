"""
worker.py - Download Engine for YouTube Downloader Pro

This module provides:
- Thread-safe download queue management
- QThread-based worker system for parallel downloads
- yt-dlp integration with progress hooks
- Pause/Resume functionality
- Failed download tracking and auto-retry
- Download history management
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
import threading

from PySide6.QtCore import QThread, Signal, QObject, QMutex, QWaitCondition
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
    error_message: str = ""
    output_path: str = ""
    item_id: str = field(default_factory=lambda: "")
    
    def __post_init__(self):
        if not self.item_id:
            self.item_id = f"{hash(self.url + str(datetime.now().timestamp()))}"


class DownloadSignals(QObject):
    """Signals for download worker communication."""
    progress_updated = Signal(str, float, str)  # item_id, progress, status_text
    download_started = Signal(str, str)  # item_id, title
    download_completed = Signal(str, str, str)  # item_id, title, output_path
    download_failed = Signal(str, str, str)  # item_id, title, error
    download_skipped = Signal(str, str)  # item_id, reason
    log_message = Signal(str)  # message
    queue_empty = Signal()
    all_workers_idle = Signal()


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
                self.signals.log_message.emit(f"[Worker {self.worker_id}] Error: {str(e)}")
    
    def _process_download(self, item: DownloadItem):
        """Process a single download item."""
        item.status = DownloadStatus.DOWNLOADING
        
        try:
            # Build yt-dlp options
            ydl_opts = self._build_ydl_options(item)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get title
                info = ydl.extract_info(item.url, download=False)
                
                if info is None:
                    raise Exception("Could not extract video information")
                
                # Handle playlist/channel
                if 'entries' in info:
                    entries = list(info['entries'])
                    total = len(entries)
                    self.signals.log_message.emit(
                        f"[Worker {self.worker_id}] Found {total} items in playlist/channel"
                    )
                    
                    for idx, entry in enumerate(entries):
                        if entry is None:
                            continue
                        if self._stop_requested:
                            break
                        
                        # Check for pause
                        self.pause_mutex.lock()
                        while self._paused and not self._stop_requested:
                            self.pause_condition.wait(self.pause_mutex)
                        self.pause_mutex.unlock()
                        
                        entry_url = entry.get('webpage_url') or entry.get('url')
                        if entry_url:
                            sub_item = DownloadItem(
                                url=entry_url,
                                mode=item.mode,
                                quality=item.quality,
                                output_dir=item.output_dir,
                                speed_limit=item.speed_limit,
                                output_format=item.output_format,
                                title=entry.get('title', f'Item {idx + 1}')
                            )
                            self._download_single(sub_item, ydl_opts)
                else:
                    item.title = info.get('title', 'Unknown')
                    self._download_single(item, ydl_opts)
            
            item.status = DownloadStatus.COMPLETED
            
        except Exception as e:
            item.status = DownloadStatus.FAILED
            item.error_message = str(e)
            self.signals.download_failed.emit(item.item_id, item.title or item.url, str(e))
            self.signals.log_message.emit(f"[Worker {self.worker_id}] Failed: {item.url} - {str(e)}")
            
            # Write to failed.txt
            self._write_failed(item)
    
    def _download_single(self, item: DownloadItem, ydl_opts: dict):
        """Download a single video/audio."""
        # Check for existing file
        if item.title:
            # Construct expected filename
            ext = item.output_format
            expected_file = Path(item.output_dir) / f"{item.title}.{ext}"
            
            if expected_file.exists():
                file_size = expected_file.stat().st_size
                if file_size > 0:  # File exists and is not empty
                    if self.duplicate_policy == "skip":
                        self.signals.download_skipped.emit(item.item_id, f"File exists: {item.title}")
                        self.signals.log_message.emit(f"[Worker {self.worker_id}] Skipped (exists): {item.title}")
                        return
                    elif self.duplicate_policy == "replace":
                        # Delete existing file to replace
                        try:
                            expected_file.unlink()
                            self.signals.log_message.emit(f"[Worker {self.worker_id}] Replacing: {item.title}")
                        except:
                            pass
                    # For "ask" policy, we just proceed (yt-dlp will overwrite)
        
        self.signals.download_started.emit(item.item_id, item.title or item.url)
        self.signals.log_message.emit(f"[Worker {self.worker_id}] Starting: {item.title or item.url}")
        
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
            # General options
            'outtmpl': output_template,
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': True,
            'no_color': True,
            
            # Network robustness
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'retry_sleep_functions': {'http': lambda n: 5 * (n + 1)},
            'source_address': '0.0.0.0',  # Force IPv4
            
            # Resume support
            'continuedl': True,
            'nooverwrites': False,
            
            # FFmpeg - auto-detect location
            'prefer_ffmpeg': True,
        }
        
        # Speed limit
        if item.speed_limit > 0:
            opts['ratelimit'] = item.speed_limit * 1024  # Convert KB/s to B/s
        
        # Audio mode
        if item.mode == DownloadMode.AUDIO:
            audio_format = item.output_format.lower()
            # Map format to codec
            codec_map = {
                'mp3': 'mp3',
                'aac': 'aac', 
                'wav': 'wav',
                'flac': 'flac'
            }
            codec = codec_map.get(audio_format, 'mp3')
            
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': codec,
                        'preferredquality': '320' if codec == 'mp3' else '0',
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,
                    },
                ],
            })
        
        # Video mode
        else:
            format_str = self._get_video_format(item.quality)
            video_format = item.output_format.lower()
            # Use the selected container format
            container = video_format if video_format in ['mp4', 'mkv', 'webm'] else 'mp4'
            
            opts.update({
                'format': format_str,
                'merge_output_format': container,
                'postprocessors': [
                    {
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': container,
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,
                    },
                ],
            })
        
        return opts
    
    def _get_video_format(self, quality: str) -> str:
        """Get yt-dlp format string for video quality."""
        quality_map = {
            'best': 'bestvideo+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best',
        }
        return quality_map.get(quality, quality_map['best'])
    
    def _write_failed(self, item: DownloadItem):
        """Write failed download to failed.txt."""
        try:
            failed_path = Path(item.output_dir).parent / 'failed.txt'
            with open(failed_path, 'a') as f:
                f.write(f"{item.url}|{item.mode.value}|{item.quality}|{item.output_dir}\n")
        except Exception as e:
            self.signals.log_message.emit(f"Failed to write to failed.txt: {e}")
    
    def _add_to_history(self, item: DownloadItem):
        """Add completed download to history.json."""
        try:
            history_path = Path(item.output_dir).parent / 'history.json'
            history = []
            
            if history_path.exists():
                with open(history_path, 'r') as f:
                    history = json.load(f)
            
            # Add new entry
            entry = {
                'title': item.title,
                'url': item.url,
                'mode': item.mode.value,
                'quality': item.quality,
                'output_path': item.output_path,
                'timestamp': datetime.now().isoformat(),
            }
            
            history.insert(0, entry)
            
            # Keep only last 50
            history = history[:50]
            
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.signals.log_message.emit(f"Failed to update history: {e}")


class DownloadManager(QObject):
    """Manages the download queue and worker threads."""
    
    # Duplicate handling policies
    DUPLICATE_ASK = "ask"
    DUPLICATE_SKIP = "skip"
    DUPLICATE_REPLACE = "replace"
    
    def __init__(self, output_dir: str = "./downloads", max_workers: int = 3):
        super().__init__()
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.duplicate_policy = self.DUPLICATE_ASK
        
        self.signals = DownloadSignals()
        self.task_queue: Queue = Queue()
        self.workers: List[DownloadWorker] = []
        self.items: Dict[str, DownloadItem] = {}
        
        self._paused = False
        self._pause_mutex = QMutex()
        self._pause_condition = QWaitCondition()
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Auto-retry failed downloads on startup
        self._retry_failed()
    
    def set_worker_count(self, count: int):
        """Set the number of parallel workers."""
        self.max_workers = max(1, min(5, count))
    
    def set_output_dir(self, path: str):
        """Set output directory."""
        self.output_dir = path
        Path(path).mkdir(parents=True, exist_ok=True)
    
    def set_duplicate_policy(self, policy: str):
        """Set duplicate file handling policy: 'ask', 'skip', or 'replace'."""
        if policy.lower() in [self.DUPLICATE_ASK, self.DUPLICATE_SKIP, self.DUPLICATE_REPLACE]:
            self.duplicate_policy = policy.lower()
    
    def add_url(self, url: str, mode: DownloadMode, quality: str = "best",
                speed_limit: int = 0, output_format: str = "mp3") -> DownloadItem:
        """Add a URL to the download queue."""
        item = DownloadItem(
            url=url.strip(),
            mode=mode,
            quality=quality,
            output_dir=self.output_dir,
            speed_limit=speed_limit,
            output_format=output_format
        )
        self.items[item.item_id] = item
        self.task_queue.put(item)
        self.signals.log_message.emit(f"Added to queue: {url}")
        return item
    
    def add_urls(self, urls: List[str], mode: DownloadMode, quality: str = "best",
                 speed_limit: int = 0) -> List[DownloadItem]:
        """Add multiple URLs to the download queue."""
        items = []
        for url in urls:
            url = url.strip()
            if url:
                item = self.add_url(url, mode, quality, speed_limit)
                items.append(item)
        return items
    
    def start(self):
        """Start the download workers."""
        self._paused = False
        
        # Start workers if not already running
        while len(self.workers) < self.max_workers:
            worker = DownloadWorker(
                worker_id=len(self.workers) + 1,
                task_queue=self.task_queue,
                signals=self.signals,
                pause_mutex=self._pause_mutex,
                pause_condition=self._pause_condition,
                duplicate_policy=self.duplicate_policy
            )
            worker.start()
            self.workers.append(worker)
        
        # Resume paused workers
        for worker in self.workers:
            worker.set_paused(False)
        
        self.signals.log_message.emit(f"Started {len(self.workers)} workers")
    
    def pause(self):
        """Pause the download queue (active downloads will complete)."""
        self._paused = True
        for worker in self.workers:
            worker.set_paused(True)
        self.signals.log_message.emit("Download queue paused")
    
    def resume(self):
        """Resume the download queue."""
        self._paused = False
        for worker in self.workers:
            worker.set_paused(False)
        self.signals.log_message.emit("Download queue resumed")
    
    def stop(self):
        """Stop all workers."""
        for worker in self.workers:
            worker.request_stop()
            worker.set_paused(False)  # Wake up if paused
        
        for worker in self.workers:
            worker.wait(5000)  # Wait up to 5 seconds
            if worker.isRunning():
                worker.terminate()
        
        self.workers.clear()
        self.signals.log_message.emit("All workers stopped")
    
    def is_paused(self) -> bool:
        """Check if queue is paused."""
        return self._paused
    
    def queue_size(self) -> int:
        """Get current queue size."""
        return self.task_queue.qsize()
    
    def _retry_failed(self):
        """Retry downloads from failed.txt on startup."""
        failed_path = Path(self.output_dir).parent / 'failed.txt'
        
        if not failed_path.exists():
            return
        
        try:
            with open(failed_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return
            
            self.signals.log_message.emit(f"Retrying {len(lines)} failed downloads...")
            
            for line in lines:
                parts = line.strip().split('|')
                if len(parts) >= 4:
                    url, mode_str, quality, output_dir = parts[:4]
                    mode = DownloadMode.AUDIO if mode_str == 'audio' else DownloadMode.VIDEO
                    self.add_url(url, mode, quality, 0)
            
            # Clear failed.txt after processing
            failed_path.unlink()
            
        except Exception as e:
            self.signals.log_message.emit(f"Error processing failed.txt: {e}")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get download history."""
        history_path = Path(self.output_dir).parent / 'history.json'
        
        if not history_path.exists():
            return []
        
        try:
            with open(history_path, 'r') as f:
                return json.load(f)
        except:
            return []
