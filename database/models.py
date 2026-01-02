"""
Database models matching the Go structs.
These are used for type hints and documentation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from bson import ObjectId


@dataclass
class User:
    """Represents a bot user in the database."""
    user_id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    files_uploaded: int = 0
    bandwidth_used: int = 0
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: datetime = field(default_factory=datetime.utcnow)
    monthly_uploads: int = 0
    monthly_reset: datetime = field(default_factory=datetime.utcnow)
    is_blocked: bool = False
    _id: Optional[ObjectId] = None


@dataclass
class File:
    """Represents an uploaded file in the database."""
    message_id: int
    user_id: int
    file_name: str
    file_size: int
    mime_type: str
    file_hash: str
    short_hash: str
    stream_link: str
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    is_revoked: bool = False
    revoked_at: Optional[datetime] = None
    access_count: int = 0
    bandwidth: int = 0
    _id: Optional[ObjectId] = None


@dataclass
class Ban:
    """Represents a banned user."""
    user_id: int
    reason: str
    banned_by: int
    banned_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    _id: Optional[ObjectId] = None


@dataclass
class Worker:
    """Represents a worker bot in the database."""
    worker_id: int
    bot_token: str
    username: str = ""
    request_count: int = 0
    is_active: bool = True
    is_dead: bool = False
    added_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)
    error_count: int = 0
    _id: Optional[ObjectId] = None


@dataclass
class StreamSession:
    """Represents an active streaming session."""
    session_id: str
    message_id: int
    user_id: int
    ip_address: str
    user_agent: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: datetime = field(default_factory=datetime.utcnow)
    bytes_sent: int = 0
    is_active: bool = True
    _id: Optional[ObjectId] = None


@dataclass
class BotStats:
    """Represents overall bot statistics."""
    total_files: int = 0
    total_bandwidth: int = 0
    total_users: int = 0
    active_users: int = 0
    total_streams: int = 0
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = None


@dataclass
class Broadcast:
    """Represents a broadcast message."""
    message_id: int
    sent_by: int
    total_users: int
    success_count: int = 0
    failed_count: int = 0
    blocked_count: int = 0
    should_pin: bool = False
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    is_complete: bool = False
    _id: Optional[ObjectId] = None


@dataclass
class ForceSubChannel:
    """Represents a force subscription channel."""
    channel_id: int
    access_hash: int
    channel_username: str
    added_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = None
