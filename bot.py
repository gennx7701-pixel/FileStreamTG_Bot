"""
FileStreamTG Bot - Main Entry Point
A Telegram bot for streaming files directly in the browser.
"""

import os
import asyncio
import logging
from config import Config
from database import connect_database, disconnect_database
from bot.client import start_bot, stop_bot
from bot.workers import start_workers, stop_workers
from web import start_web_server, stop_web_server
from utils.logger import setup_logger

# Suppress verbose logging from libraries
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)

# Set up our logger
logger = setup_logger("FileStreamBot", logging.INFO if not Config.DEV else logging.DEBUG)


async def main():
    """Main async entry point."""
    logger.info("=" * 50)
    logger.info("FileStreamTG Bot v%s Starting...", Config.BOT_VERSION)
    logger.info("=" * 50)
    
    # Validate required config
    if not Config.API_ID or not Config.API_HASH:
        logger.error("API_ID and API_HASH are required!")
        return
    
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN is required!")
        return
    
    if not Config.LOG_CHANNEL:
        logger.error("LOG_CHANNEL is required!")
        return
    
    if not Config.MONGODB_URI:
        logger.error("MONGODB_URI is required!")
        return
    
    try:
        # Connect to database
        await connect_database()
        
        # Start main bot FIRST (this resolves and caches LOG_CHANNEL)
        # Workers need the resolved channel ID before they can cache it
        await start_bot()
        
        # Start worker bots AFTER main bot has resolved the log channel
        await start_workers()
        
        # Cache the log channel for all workers
        from bot.workers import cache_log_channel_for_workers
        await cache_log_channel_for_workers()
        
        # Start web server
        await start_web_server()
        
        logger.info("=" * 50)
        logger.info("Bot is running! Press Ctrl+C to stop.")
        logger.info("Web server: %s", Config.HOST)
        logger.info("=" * 50)
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        
    except Exception as e:
        logger.error("Fatal error: %s", e)
        raise
        
    finally:
        # Cleanup
        await stop_web_server()
        await stop_bot()
        await stop_workers()
        await disconnect_database()
        logger.info("Bot stopped")


if __name__ == "__main__":
    # Create sessions directory if not exists
    os.makedirs("sessions", exist_ok=True)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
