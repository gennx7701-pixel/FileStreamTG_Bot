"""
Database package for MongoDB operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

# Global database client and database objects
client: AsyncIOMotorClient = None
db = None

# Collection names
USERS_COLLECTION = "users"
FILES_COLLECTION = "files"
BANS_COLLECTION = "bans"
WORKERS_COLLECTION = "workers"
SESSIONS_COLLECTION = "sessions"
BROADCASTS_COLLECTION = "broadcasts"
FORCESUB_COLLECTION = "forcesub"


async def connect_database():
    """Connect to MongoDB and create indexes."""
    global client, db
    
    logger.info("Connecting to MongoDB...")
    
    client = AsyncIOMotorClient(Config.MONGODB_URI)
    db = client[Config.DATABASE_NAME]
    
    # Ping to verify connection
    await client.admin.command('ping')
    
    # Create indexes
    await create_indexes()
    
    logger.info("Connected to MongoDB successfully")
    return db


async def create_indexes():
    """Create necessary indexes for collections."""
    try:
        # Users collection - unique user_id index
        await db[USERS_COLLECTION].create_index("user_id", unique=True)
        
        # Files collection - multiple indexes
        await db[FILES_COLLECTION].create_index("message_id")
        await db[FILES_COLLECTION].create_index("user_id")
        await db[FILES_COLLECTION].create_index("short_hash")
        await db[FILES_COLLECTION].create_index([("uploaded_at", -1)])
        
        # Bans collection
        await db[BANS_COLLECTION].create_index("user_id")
        
        # Sessions collection with TTL
        await db[SESSIONS_COLLECTION].create_index("session_id")
        await db[SESSIONS_COLLECTION].create_index("is_active")
        await db[SESSIONS_COLLECTION].create_index(
            "last_active_at",
            expireAfterSeconds=3600  # TTL: expire after 1 hour of inactivity
        )
        
        # Workers collection
        await db[WORKERS_COLLECTION].create_index("worker_id", unique=True)
        
        # Force sub collection
        await db[FORCESUB_COLLECTION].create_index("channel_id", unique=True)
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Failed to create some indexes: {e}")


async def disconnect_database():
    """Disconnect from MongoDB."""
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


def get_collection(name: str):
    """Get a collection by name."""
    return db[name]
