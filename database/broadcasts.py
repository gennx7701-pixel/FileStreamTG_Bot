"""
Broadcast database operations.
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId
from database import get_collection, BROADCASTS_COLLECTION


async def create_broadcast(
    message_id: int,
    sent_by: int,
    total_users: int,
    should_pin: bool = False
) -> dict:
    """Create a new broadcast record."""
    collection = get_collection(BROADCASTS_COLLECTION)
    
    broadcast_data = {
        "message_id": message_id,
        "sent_by": sent_by,
        "total_users": total_users,
        "success_count": 0,
        "failed_count": 0,
        "blocked_count": 0,
        "should_pin": should_pin,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "is_complete": False
    }
    
    result = await collection.insert_one(broadcast_data)
    broadcast_data["_id"] = result.inserted_id
    return broadcast_data


async def update_broadcast_progress(
    broadcast_id: ObjectId,
    success_count: int,
    failed_count: int,
    blocked_count: int
) -> None:
    """Update broadcast progress."""
    collection = get_collection(BROADCASTS_COLLECTION)
    
    await collection.update_one(
        {"_id": broadcast_id},
        {
            "$set": {
                "success_count": success_count,
                "failed_count": failed_count,
                "blocked_count": blocked_count
            }
        }
    )


async def complete_broadcast(broadcast_id: ObjectId) -> None:
    """Mark a broadcast as complete."""
    collection = get_collection(BROADCASTS_COLLECTION)
    
    await collection.update_one(
        {"_id": broadcast_id},
        {
            "$set": {
                "is_complete": True,
                "completed_at": datetime.utcnow()
            }
        }
    )


async def get_broadcast(broadcast_id: ObjectId) -> Optional[dict]:
    """Get a broadcast by ID."""
    collection = get_collection(BROADCASTS_COLLECTION)
    return await collection.find_one({"_id": broadcast_id})
