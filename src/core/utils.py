import re
from typing import List

def extract_youtube_urls(text: str) -> List[str]:
    """
    Extract YouTube URLs from any text input.
    Handles various YouTube URL formats:
    - youtube.com/watch?v=
    - youtu.be/
    - youtube.com/playlist?list=
    - youtube.com/shorts/
    - youtube.com/@channel
    - youtube.com/channel/
    """
    patterns = [
        # Standard watch URLs
        r'https?://(?:www\.)?youtube\.com/watch\?[^\s<>"\']+',
        # Short URLs
        r'https?://youtu\.be/[a-zA-Z0-9_-]+(?:\?[^\s<>"\']*)?',
        # Playlist URLs
        r'https?://(?:www\.)?youtube\.com/playlist\?[^\s<>"\']+',
        # Shorts
        r'https?://(?:www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]+',
        # Channel URLs
        r'https?://(?:www\.)?youtube\.com/@[^\s<>"\'/]+',
        r'https?://(?:www\.)?youtube\.com/channel/[^\s<>"\']+',
        r'https?://(?:www\.)?youtube\.com/c/[^\s<>"\']+',
        # Music URLs
        r'https?://music\.youtube\.com/watch\?[^\s<>"\']+',
    ]
    
    urls = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        # Clean URL (remove trailing punctuation)
        url = url.rstrip('.,;:!?')
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls

import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
