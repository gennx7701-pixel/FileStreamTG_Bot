"""
Ban database operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from database import get_collection, BANS_COLLECTION


async def ban_user(
    user_id: int,
    banned_by: int,
    reason: str,
    duration: Optional[timedelta] = None
) -> None:
    """Ban a user."""
    collection = get_collection(BANS_COLLECTION)
    
    expires_at = None
    if duration:
        expires_at = datetime.utcnow() + duration
    
    ban_data = {
        "user_id": user_id,
        "reason": reason,
        "banned_by": banned_by,
        "banned_at": datetime.utcnow(),
        "expires_at": expires_at,
        "is_active": True
    }
    
    # Update existing ban or create new one
    await collection.update_one(
        {"user_id": user_id},
        {"$set": ban_data},
        upsert=True
    )


async def unban_user(user_id: int) -> None:
    """Unban a user."""
    collection = get_collection(BANS_COLLECTION)
    
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"is_active": False}}
    )


async def is_user_banned(user_id: int) -> Tuple[bool, Optional[dict]]:
    """Check if a user is banned."""
    collection = get_collection(BANS_COLLECTION)
    
    ban = await collection.find_one({
        "user_id": user_id,
        "is_active": True
    })
    
    if ban is None:
        return False, None
    
    # Check if ban has expired
    if ban.get("expires_at") and ban["expires_at"] < datetime.utcnow():
        # Auto-unban expired bans
        await unban_user(user_id)
        return False, None
    
    return True, ban


async def get_banned_users() -> List[dict]:
    """Get all currently banned users."""
    collection = get_collection(BANS_COLLECTION)
    
    cursor = collection.find({"is_active": True}).sort("banned_at", -1)
    return await cursor.to_list(length=None)


async def get_ban_count() -> int:
    """Get count of active bans."""
    collection = get_collection(BANS_COLLECTION)
    return await collection.count_documents({"is_active": True})
