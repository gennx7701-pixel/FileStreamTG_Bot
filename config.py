import os
import re
import socket
import requests
from dotenv import load_dotenv

# Load environment variables from fsb.env file
load_dotenv("fsb.env")


def _parse_user_list(value: str) -> list:
    """Parse comma-separated user IDs into a list of integers."""
    if not value:
        return []
    try:
        return [int(uid.strip()) for uid in value.split(",") if uid.strip()]
    except ValueError:
        return []


def _parse_channel_list(value: str) -> list:
    """Parse comma-separated channel usernames into a list."""
    if not value:
        return []
    channels = []
    for ch in value.split(","):
        ch = ch.strip()
        if ch:
            if not ch.startswith("@"):
                ch = "@" + ch
            channels.append(ch)
    return channels


def _get_multi_tokens() -> list:
    """Get all MULTI_TOKEN environment variables."""
    tokens = []
    pattern = re.compile(r"MULTI_TOKEN\d+")
    for key, value in os.environ.items():
        if pattern.match(key) and value:
            tokens.append(value)
    return tokens


def _get_internal_ip() -> str:
    """Get the internal IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def _get_public_ip() -> str:
    """Get the public IP address."""
    try:
        response = requests.get("https://api.ipify.org?format=text", timeout=5)
        return response.text.strip()
    except Exception:
        return "localhost"


def _parse_log_channel(value: str):
    """Parse LOG_CHANNEL - can be @username or numeric ID."""
    if not value:
        return 0
    value = value.strip()
    # If it starts with @ or is not a number, treat as username
    if value.startswith("@") or not value.lstrip("-").isdigit():
        return value
    # Otherwise, convert to int
    return int(value)


class Config:
    """Configuration class that loads settings from environment variables."""
    
    # Telegram API credentials
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # Log channel for storing files (can be @username or numeric ID)
    LOG_CHANNEL = _parse_log_channel(os.getenv("LOG_CHANNEL", ""))
    
    # Development mode
    DEV = os.getenv("DEV", "false").lower() == "true"
    
    # Server settings
    PORT = int(os.getenv("PORT", 8080))
    HOST = os.getenv("HOST", "")
    
    # Hash settings for links
    HASH_LENGTH = int(os.getenv("HASH_LENGTH", 6))
    
    # Session settings
    USE_SESSION_FILE = os.getenv("USE_SESSION_FILE", "true").lower() == "true"
    USER_SESSION = os.getenv("USER_SESSION", "")
    
    # IP settings
    USE_PUBLIC_IP = os.getenv("USE_PUBLIC_IP", "false").lower() == "true"
    
    # User restrictions
    ALLOWED_USERS = _parse_user_list(os.getenv("ALLOWED_USERS", ""))
    ADMIN_USERS = _parse_user_list(os.getenv("ADMIN_USERS", ""))
    
    # MongoDB settings
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "filestream_bot")
    
    # File limits
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 2147483648))  # 2GB default
    MONTHLY_LIMIT = int(os.getenv("MONTHLY_LIMIT", 100))
    
    # Support info
    SUPPORT_INFO = os.getenv("SUPPORT_INFO", "Contact @admin for support")
    
    # Force subscription channels
    FORCE_SUB_CHANNELS = _parse_channel_list(os.getenv("FORCE_SUB_CHANNELS", ""))
    
    # Multi-token workers
    MULTI_TOKENS = _get_multi_tokens()
    
    # Bot version
    BOT_VERSION = "2.0.0"


def setup_host():
    """Set up the HOST configuration if not provided."""
    if not Config.HOST:
        if Config.USE_PUBLIC_IP:
            ip = _get_public_ip()
        else:
            ip = _get_internal_ip()
        Config.HOST = f"http://{ip}:{Config.PORT}"
    
    # Validate hash length
    if Config.HASH_LENGTH < 5:
        Config.HASH_LENGTH = 6
    elif Config.HASH_LENGTH > 32:
        Config.HASH_LENGTH = 32


# Set up host on module load
setup_host()
