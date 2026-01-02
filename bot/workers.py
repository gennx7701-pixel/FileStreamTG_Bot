"""
Worker bot management for increased streaming capacity.
"""

from typing import List, Optional
from pyrogram import Client
from pyrogram.raw import functions
from pyrogram.raw.types import InputChannel, InputPeerChannel
from config import Config
from utils.logger import logger

# List of worker clients
workers: List[Client] = []
current_worker_index: int = 0

# Cached log channel info for workers
_log_channel_id: Optional[int] = None
_log_channel_access_hash: Optional[int] = None


async def start_workers() -> List[Client]:
    """Initialize and start all worker bots."""
    global workers
    
    if not Config.MULTI_TOKENS:
        logger.info("No worker bots configured")
        return []
    
    logger.info(f"Starting {len(Config.MULTI_TOKENS)} worker bots...")
    
    for i, token in enumerate(Config.MULTI_TOKENS):
        try:
            worker = Client(
                name=f"worker_{i + 1}",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=token,
                workdir="sessions",
                no_updates=True  # Workers don't need to receive updates
            )
            
            await worker.start()
            
            me = await worker.get_me()
            logger.info(f"Worker {i + 1} started as @{me.username}")
            
            workers.append(worker)
            
        except Exception as e:
            logger.error(f"Failed to start worker {i + 1}: {e}")
    
    logger.info(f"Started {len(workers)} worker bots")
    return workers


async def cache_log_channel_for_workers():
    """Cache the log channel for all workers after main bot has resolved it."""
    global _log_channel_id, _log_channel_access_hash
    
    if not workers:
        logger.info("No workers to cache log channel for")
        return
    
    # Get resolved channel info from main bot
    from bot.client import StreamBot, log_channel_peer
    
    if not log_channel_peer:
        logger.error("Log channel peer not available from main bot")
        return
    
    # Store channel info for later use
    _log_channel_id = log_channel_peer.id
    
    logger.info(f"Caching log channel (ID: {_log_channel_id}) for {len(workers)} workers...")
    
    for i, worker in enumerate(workers):
        worker_username = "unknown"
        try:
            me = await worker.get_me()
            worker_username = me.username
        except:
            pass
            
        cached = False
        
        # Method 1: Try get_chat
        try:
            chat = await worker.get_chat(Config.LOG_CHANNEL)
            logger.info(f"Worker {i + 1} (@{worker_username}) cached log channel: {chat.title}")
            cached = True
        except Exception as e:
            logger.warning(f"Worker {i + 1} get_chat failed: {e}")
        
        # Method 2: Try get_chat_history (works for private channels if bot is admin)
        if not cached:
            try:
                async for msg in worker.get_chat_history(Config.LOG_CHANNEL, limit=1):
                    pass
                logger.info(f"Worker {i + 1} (@{worker_username}) cached log channel via history")
                cached = True
            except Exception as e2:
                logger.warning(f"Worker {i + 1} get_chat_history failed: {e2}")
        
        # Method 3: Try sending and deleting a message
        if not cached:
            try:
                test_msg = await worker.send_message(Config.LOG_CHANNEL, "🔄 Worker bot initializing...")
                await test_msg.delete()
                logger.info(f"Worker {i + 1} (@{worker_username}) cached log channel via test message")
                cached = True
            except Exception as e3:
                logger.warning(f"Worker {i + 1} send_message failed: {e3}")
        
        if not cached:
            logger.error(f"")
            logger.error(f"❌ Worker {i + 1} (@{worker_username}) FAILED to cache log channel!")
            logger.error(f"   Make sure this bot is an ADMIN in the log channel!")
            logger.error(f"   The bot needs 'Post Messages' and 'Delete Messages' permissions.")
            logger.error(f"")


async def stop_workers():
    """Stop all worker bots."""
    global workers
    
    for i, worker in enumerate(workers):
        try:
            await worker.stop()
            logger.info(f"Worker {i + 1} stopped")
        except Exception as e:
            logger.error(f"Failed to stop worker {i + 1}: {e}")
    
    workers = []


def get_next_worker() -> Client:
    """
    Get the next worker client in round-robin fashion.
    Falls back to main bot if no workers available.
    """
    global current_worker_index
    
    if not workers:
        # Import here to avoid circular import
        from bot.client import StreamBot
        return StreamBot
    
    worker = workers[current_worker_index]
    current_worker_index = (current_worker_index + 1) % len(workers)
    
    return worker


def get_main_bot() -> Client:
    """Get the main bot client (preferred for peer resolution)."""
    from bot.client import StreamBot
    return StreamBot


def get_worker_count() -> int:
    """Get the number of active workers."""
    return len(workers)


def get_log_channel_id() -> Optional[int]:
    """Get the cached log channel ID."""
    return _log_channel_id
