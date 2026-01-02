"""
User database operations.
"""

from datetime import datetime
from typing import Optional, List
from database import get_collection, USERS_COLLECTION


async def get_or_create_user(
    user_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = ""
) -> dict:
    """Get or create a user record."""
    collection = get_collection(USERS_COLLECTION)
    
    user = await collection.find_one({"user_id": user_id})
    
    if user is None:
        # Create new user
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        user = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "files_uploaded": 0,
            "bandwidth_used": 0,
            "joined_at": now,
            "last_active_at": now,
            "monthly_uploads": 0,
            "monthly_reset": month_start,
            "is_blocked": False
        }
        
        result = await collection.insert_one(user)
        user["_id"] = result.inserted_id
        return user
    
    # Update user info and last active
    now = datetime.utcnow()
    update = {
        "$set": {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "last_active_at": now
        }
    }
    
    # Check if monthly reset is needed
    month_start = datetime(now.year, now.month, 1)
    if user.get("monthly_reset", datetime.min) < month_start:
        update["$set"]["monthly_uploads"] = 0
        update["$set"]["monthly_reset"] = month_start
    
    await collection.update_one({"user_id": user_id}, update)
    
    # Refetch updated user
    return await collection.find_one({"user_id": user_id})


async def get_user(user_id: int) -> Optional[dict]:
    """Get a user by ID."""
    collection = get_collection(USERS_COLLECTION)
    return await collection.find_one({"user_id": user_id})


async def update_user_stats(user_id: int) -> None:
    """Update user statistics after file upload."""
    collection = get_collection(USERS_COLLECTION)
    
    await collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "files_uploaded": 1,
                "monthly_uploads": 1
            },
            "$set": {
                "last_active_at": datetime.utcnow()
            }
        }
    )


async def update_user_bandwidth(user_id: int, bytes_used: int) -> None:
    """Update user bandwidth usage."""
    collection = get_collection(USERS_COLLECTION)
    
    await collection.update_one(
        {"user_id": user_id},
        {"$inc": {"bandwidth_used": bytes_used}}
    )


async def get_all_users() -> List[dict]:
    """Get all non-blocked users (for broadcast)."""
    collection = get_collection(USERS_COLLECTION)
    
    cursor = collection.find({"is_blocked": False})
    return await cursor.to_list(length=None)


async def get_user_count() -> int:
    """Get total user count."""
    collection = get_collection(USERS_COLLECTION)
    return await collection.count_documents({})


async def get_active_user_count() -> int:
    """Get count of users active in last 30 days."""
    collection = get_collection(USERS_COLLECTION)
    
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    return await collection.count_documents({
        "last_active_at": {"$gte": thirty_days_ago}
    })


async def mark_user_blocked(user_id: int) -> None:
    """Mark a user as blocked (deleted bot)."""
    collection = get_collection(USERS_COLLECTION)
    
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"is_blocked": True}}
    )


async def delete_user(user_id: int) -> None:
    """Delete a user from the database."""
    collection = get_collection(USERS_COLLECTION)
    await collection.delete_one({"user_id": user_id})


async def get_users_paginated(page: int, limit: int) -> tuple:
    """Get users with pagination."""
    collection = get_collection(USERS_COLLECTION)
    
    total = await collection.count_documents({})
    
    cursor = collection.find({}).sort("joined_at", -1).skip((page - 1) * limit).limit(limit)
    users = await cursor.to_list(length=limit)
    
    return users, total
