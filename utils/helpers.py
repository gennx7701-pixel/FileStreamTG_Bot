"""
Helper utility functions.
"""

from datetime import timedelta
from typing import List, TypeVar, Optional
from config import Config

T = TypeVar('T')


def contains(lst: List[T], item: T) -> bool:
    """Check if item is in list."""
    return item in lst


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in Config.ADMIN_USERS


def format_bytes(bytes_size: int) -> str:
    """Convert bytes to human readable format."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    
    units = ["KB", "MB", "GB", "TB", "PB"]
    size = bytes_size / 1024
    unit_idx = 0
    
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    
    return f"{size:.2f} {units[unit_idx]}"


def format_file_size(bytes_size: int) -> str:
    """Convert bytes to human readable file size."""
    if bytes_size < 1024:
        return "1 B"
    
    units = ["KB", "MB", "GB", "TB"]
    size = bytes_size / 1024
    unit_idx = 0
    
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    
    return f"{size:.1f} {units[unit_idx]}"


def format_duration(duration: timedelta) -> str:
    """Format duration to human readable string."""
    total_seconds = int(duration.total_seconds())
    
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def create_progress_bar(percent: float, length: int = 10) -> str:
    """Create an ASCII progress bar."""
    filled = int(percent / 100 * length)
    filled = max(0, min(filled, length))
    
    bar = "█" * filled + "░" * (length - filled)
    return bar


def parse_duration(duration_str: str) -> Optional[timedelta]:
    """
    Parse duration string to timedelta.
    Format: 1h, 1d, 1w, 1m (hours, days, weeks, months)
    """
    if len(duration_str) < 2:
        return None
    
    try:
        value = int(duration_str[:-1])
        unit = duration_str[-1].lower()
        
        if unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        elif unit == 'm':
            return timedelta(days=value * 30)
        else:
            return None
            
    except ValueError:
        return None


def truncate_string(s: str, max_len: int) -> str:
    """Truncate string with ellipsis if too long."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


def mask_ip(ip: str) -> str:
    """Mask the last octet of an IP address for privacy."""
    parts = ip.split('.')
    if len(parts) == 4:
        parts[-1] = '***'
        return '.'.join(parts)
    return ip


def extract_telegram_link(text: str) -> Optional[str]:
    """Extract a Telegram link from text."""
    patterns = ["https://t.me/", "http://t.me/", "t.me/"]
    
    for pattern in patterns:
        if pattern in text:
            idx = text.find(pattern)
            end = idx + len(pattern)
            
            # Find end of link
            while end < len(text) and not text[end].isspace():
                end += 1
            
            link = text[idx:end]
            if not link.startswith("http"):
                link = "https://" + link
            return link
    
    return None


def extract_username(text: str) -> Optional[str]:
    """Extract a Telegram @username from text."""
    if "@" not in text:
        return None
    
    idx = text.find("@")
    end = idx + 1
    
    while end < len(text) and (text[end].isalnum() or text[end] == '_'):
        end += 1
    
    if end > idx + 1:
        return text[idx + 1:end]
    
    return None
