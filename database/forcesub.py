"""
Force subscription channel database operations.
"""

from datetime import datetime
from typing import List, Optional
from database import get_collection, FORCESUB_COLLECTION


async def add_forcesub_channel(
    channel_id: int,
    access_hash: int,
    channel_username: str
) -> None:
    """Add a force subscription channel."""
    collection = get_collection(FORCESUB_COLLECTION)
    
    channel_data = {
        "channel_id": channel_id,
        "access_hash": access_hash,
        "channel_username": channel_username,
        "added_at": datetime.utcnow()
    }
    
    await collection.update_one(
        {"channel_id": channel_id},
        {"$set": channel_data},
        upsert=True
    )


async def remove_forcesub_channel(channel_username: str) -> bool:
    """Remove a force subscription channel."""
    collection = get_collection(FORCESUB_COLLECTION)
    
    # Normalize username
    if not channel_username.startswith("@"):
        channel_username = "@" + channel_username
    
    result = await collection.delete_one({"channel_username": channel_username})
    return result.deleted_count > 0


async def get_forcesub_channels() -> List[dict]:
    """Get all force subscription channels."""
    collection = get_collection(FORCESUB_COLLECTION)
    
    cursor = collection.find({})
    return await cursor.to_list(length=None)


async def get_forcesub_channel(channel_username: str) -> Optional[dict]:
    """Get a specific force subscription channel."""
    collection = get_collection(FORCESUB_COLLECTION)
    
    if not channel_username.startswith("@"):
        channel_username = "@" + channel_username
    
    return await collection.find_one({"channel_username": channel_username})
