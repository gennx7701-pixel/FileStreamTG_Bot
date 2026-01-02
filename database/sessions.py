"""
Streaming session database operations.
"""

from datetime import datetime
from typing import List, Optional
from database import get_collection, SESSIONS_COLLECTION


async def create_session(
    session_id: str,
    message_id: int,
    user_id: int,
    ip_address: str,
    user_agent: str
) -> dict:
    """Create a new streaming session."""
    collection = get_collection(SESSIONS_COLLECTION)
    
    now = datetime.utcnow()
    session_data = {
        "session_id": session_id,
        "message_id": message_id,
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "started_at": now,
        "last_active_at": now,
        "bytes_sent": 0,
        "is_active": True
    }
    
    result = await collection.insert_one(session_data)
    session_data["_id"] = result.inserted_id
    return session_data


async def update_session(session_id: str, bytes_sent: int) -> None:
    """Update session with bytes sent."""
    collection = get_collection(SESSIONS_COLLECTION)
    
    await collection.update_one(
        {"session_id": session_id},
        {
            "$inc": {"bytes_sent": bytes_sent},
            "$set": {"last_active_at": datetime.utcnow()}
        }
    )


async def end_session(session_id: str) -> None:
    """Mark a session as ended."""
    collection = get_collection(SESSIONS_COLLECTION)
    
    await collection.update_one(
        {"session_id": session_id},
        {"$set": {"is_active": False}}
    )


async def get_active_sessions() -> List[dict]:
    """Get all active streaming sessions."""
    collection = get_collection(SESSIONS_COLLECTION)
    
    cursor = collection.find({"is_active": True}).sort("started_at", -1)
    return await cursor.to_list(length=None)


async def get_active_session_count() -> int:
    """Get count of active sessions."""
    collection = get_collection(SESSIONS_COLLECTION)
    return await collection.count_documents({"is_active": True})


async def get_session(session_id: str) -> Optional[dict]:
    """Get a session by ID."""
    collection = get_collection(SESSIONS_COLLECTION)
    return await collection.find_one({"session_id": session_id})
