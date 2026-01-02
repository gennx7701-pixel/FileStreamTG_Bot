"""
File property extraction from Telegram messages.
"""

from typing import Optional, Dict, Any
from pyrogram.types import Message
from pyrogram.file_id import FileId


def get_media_from_message(message: Message) -> Optional[Any]:
    """Get the media object from a message."""
    media_types = [
        "document",
        "video",
        "audio",
        "voice",
        "video_note",
        "photo",
        "animation",
        "sticker"
    ]
    
    for media_type in media_types:
        media = getattr(message, media_type, None)
        if media:
            return media
    
    return None


def get_file_id(message: Message) -> Optional[str]:
    """Get file_id from a message."""
    media = get_media_from_message(message)
    if media:
        # For photos, it's a list - get the largest
        if isinstance(media, list):
            return media[-1].file_id if media else None
        return getattr(media, "file_id", None)
    return None


def get_file_unique_id(message: Message) -> Optional[str]:
    """Get file_unique_id from a message."""
    media = get_media_from_message(message)
    if media:
        if isinstance(media, list):
            return media[-1].file_unique_id if media else None
        return getattr(media, "file_unique_id", None)
    return None


def get_file_name(message: Message) -> str:
    """Get file name from a message."""
    media = get_media_from_message(message)
    
    if media is None:
        return "unknown"
    
    # For photos
    if isinstance(media, list):
        return f"photo_{message.id}.jpg"
    
    # Try to get file_name attribute
    file_name = getattr(media, "file_name", None)
    if file_name:
        return file_name
    
    # Generate name based on media type
    if message.video:
        return f"video_{message.id}.mp4"
    elif message.audio:
        return f"audio_{message.id}.mp3"
    elif message.voice:
        return f"voice_{message.id}.ogg"
    elif message.video_note:
        return f"video_note_{message.id}.mp4"
    elif message.animation:
        return f"animation_{message.id}.mp4"
    elif message.sticker:
        return f"sticker_{message.id}.webp"
    elif message.document:
        return f"document_{message.id}"
    
    return f"file_{message.id}"


def get_file_size(message: Message) -> int:
    """Get file size from a message."""
    media = get_media_from_message(message)
    
    if media is None:
        return 0
    
    # For photos
    if isinstance(media, list):
        return media[-1].file_size if media else 0
    
    return getattr(media, "file_size", 0) or 0


def get_mime_type(message: Message) -> str:
    """Get MIME type from a message."""
    media = get_media_from_message(message)
    
    if media is None:
        return "application/octet-stream"
    
    # For photos
    if isinstance(media, list):
        return "image/jpeg"
    
    mime_type = getattr(media, "mime_type", None)
    if mime_type:
        return mime_type
    
    # Infer from message type
    if message.video:
        return "video/mp4"
    elif message.audio:
        return "audio/mpeg"
    elif message.voice:
        return "audio/ogg"
    elif message.video_note:
        return "video/mp4"
    elif message.animation:
        return "video/mp4"
    elif message.sticker:
        return "image/webp"
    
    return "application/octet-stream"


def get_file_properties(message: Message) -> Dict[str, Any]:
    """Extract all file properties from a message."""
    media = get_media_from_message(message)
    
    # Get the numeric file ID for hashing
    file_id_str = get_file_id(message)
    file_id_num = 0
    if file_id_str:
        try:
            decoded = FileId.decode(file_id_str)
            file_id_num = decoded.media_id
        except Exception:
            # Fallback to message ID
            file_id_num = message.id
    
    return {
        "file_id": get_file_id(message),
        "file_unique_id": get_file_unique_id(message),
        "file_name": get_file_name(message),
        "file_size": get_file_size(message),
        "mime_type": get_mime_type(message),
        "file_id_num": file_id_num
    }


def is_supported_media(message: Message) -> bool:
    """Check if the message contains supported media."""
    return get_media_from_message(message) is not None
