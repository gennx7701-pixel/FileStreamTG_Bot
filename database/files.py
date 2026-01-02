"""
File database operations.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from database import get_collection, FILES_COLLECTION


async def create_file(file_data: dict) -> dict:
    """Create a new file record."""
    collection = get_collection(FILES_COLLECTION)
    
    file_data["uploaded_at"] = datetime.utcnow()
    file_data["is_revoked"] = False
    file_data["access_count"] = 0
    file_data["bandwidth"] = 0
    
    result = await collection.insert_one(file_data)
    file_data["_id"] = result.inserted_id
    return file_data


async def get_file_by_message_id(message_id: int) -> Optional[dict]:
    """Get a file by message ID."""
    collection = get_collection(FILES_COLLECTION)
    return await collection.find_one({"message_id": message_id})


async def get_file_by_hash(short_hash: str) -> Optional[dict]:
    """Get a file by short hash."""
    collection = get_collection(FILES_COLLECTION)
    return await collection.find_one({"short_hash": short_hash})


async def get_user_files(user_id: int, page: int, limit: int) -> Tuple[List[dict], int]:
    """Get files uploaded by a user with pagination."""
    collection = get_collection(FILES_COLLECTION)
    
    filter_query = {"user_id": user_id}
    
    total = await collection.count_documents(filter_query)
    
    cursor = collection.find(filter_query).sort("uploaded_at", -1).skip((page - 1) * limit).limit(limit)
    files = await cursor.to_list(length=limit)
    
    return files, total


async def get_user_active_files(
    user_id: int, 
    page: int, 
    per_page: int, 
    max_files: int = 40
) -> Tuple[List[dict], int]:
    """Get only non-revoked files with pagination."""
    collection = get_collection(FILES_COLLECTION)
    
    filter_query = {"user_id": user_id, "is_revoked": False}
    
    total = await collection.count_documents(filter_query)
    
    cursor = collection.find(filter_query).sort("uploaded_at", -1).skip((page - 1) * per_page).limit(per_page)
    files = await cursor.to_list(length=per_page)
    
    return files, total


async def get_user_file_count(user_id: int) -> int:
    """Get the number of files uploaded by a user."""
    collection = get_collection(FILES_COLLECTION)
    return await collection.count_documents({"user_id": user_id})


async def get_user_monthly_file_count(user_id: int) -> int:
    """Get files uploaded this month."""
    collection = get_collection(FILES_COLLECTION)
    
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    return await collection.count_documents({
        "user_id": user_id,
        "uploaded_at": {"$gte": month_start}
    })


async def get_total_file_count() -> int:
    """Get total files count."""
    collection = get_collection(FILES_COLLECTION)
    return await collection.count_documents({})


async def get_total_bandwidth() -> int:
    """Get total bandwidth used."""
    collection = get_collection(FILES_COLLECTION)
    
    pipeline = [
        {"$group": {"_id": None, "total_bandwidth": {"$sum": "$bandwidth"}}}
    ]
    
    result = await collection.aggregate(pipeline).to_list(length=1)
    
    if result:
        return result[0].get("total_bandwidth", 0)
    return 0


async def revoke_file(message_id: int) -> None:
    """Mark a file as revoked."""
    collection = get_collection(FILES_COLLECTION)
    
    await collection.update_one(
        {"message_id": message_id},
        {
            "$set": {
                "is_revoked": True,
                "revoked_at": datetime.utcnow()
            }
        }
    )


async def revoke_user_files(user_id: int) -> int:
    """Revoke all files for a user."""
    collection = get_collection(FILES_COLLECTION)
    
    result = await collection.update_many(
        {"user_id": user_id, "is_revoked": False},
        {
            "$set": {
                "is_revoked": True,
                "revoked_at": datetime.utcnow()
            }
        }
    )
    
    return result.modified_count


async def is_file_revoked(message_id: int) -> bool:
    """Check if a file is revoked."""
    file = await get_file_by_message_id(message_id)
    if file:
        return file.get("is_revoked", False)
    return False


async def update_file_access(message_id: int, bytes_sent: int) -> None:
    """Update file access statistics."""
    collection = get_collection(FILES_COLLECTION)
    
    await collection.update_one(
        {"message_id": message_id},
        {
            "$inc": {
                "access_count": 1,
                "bandwidth": bytes_sent
            }
        }
    )


async def get_user_bandwidth(user_id: int) -> int:
    """Get total bandwidth used by a user."""
    collection = get_collection(FILES_COLLECTION)
    
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total_bandwidth": {"$sum": "$bandwidth"}}}
    ]
    
    result = await collection.aggregate(pipeline).to_list(length=1)
    
    if result:
        return result[0].get("total_bandwidth", 0)
    return 0


async def get_total_stream_count() -> int:
    """Get total stream/access count across all files."""
    collection = get_collection(FILES_COLLECTION)
    
    pipeline = [
        {"$group": {"_id": None, "total_streams": {"$sum": "$access_count"}}}
    ]
    
    result = await collection.aggregate(pipeline).to_list(length=1)
    
    if result:
        return result[0].get("total_streams", 0)
    return 0
