"""
Main Pyrogram client for the bot.
"""

from pyrogram import Client
from pyrogram.errors import PeerIdInvalid, ChannelInvalid
from config import Config
from utils.logger import logger

StreamBot: Client = None
bot_username: str = ""
log_channel_peer = None  # Cached log channel peer


async def start_bot() -> Client:
    """Initialize and start the main bot client."""
    global StreamBot, bot_username, log_channel_peer
    
    logger.info("Starting Telegram Bot...")
    
    StreamBot = Client(
        name="FileStreamBot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins={"root": "plugins"},
        workdir="sessions"
    )
    
    await StreamBot.start()
    
    # Get bot info
    me = await StreamBot.get_me()
    bot_username = me.username
    
    logger.info(f"Bot started as @{bot_username}")
    
    # Cache the log channel
    log_channel_id = Config.LOG_CHANNEL
    
    try:
        log_channel = None
        
        # Check if LOG_CHANNEL is a username (string starting with @) or ID
        if isinstance(log_channel_id, str) and (log_channel_id.startswith("@") or not log_channel_id.lstrip("-").isdigit()):
            # It's a username - use directly
            logger.info(f"Resolving log channel by username: {log_channel_id}")
            log_channel = await StreamBot.get_chat(log_channel_id)
        else:
            # It's an ID - try to resolve
            logger.info(f"Resolving log channel by ID: {log_channel_id}")
            try:
                log_channel = await StreamBot.get_chat(log_channel_id)
            except (ValueError, PeerIdInvalid, ChannelInvalid) as e:
                # Peer validation failed - try alternative methods
                logger.warning(f"Direct get_chat failed: {e}")
                
                # Try to send a test message and delete it to cache the peer
                try:
                    logger.info("Attempting to cache peer via test message...")
                    test_msg = await StreamBot.send_message(log_channel_id, "Bot starting - testing channel access...")
                    await test_msg.delete()
                    log_channel = await StreamBot.get_chat(log_channel_id)
                    logger.info("Successfully cached peer via test message")
                except Exception as e2:
                    logger.error(f"Test message method also failed: {e2}")
                    logger.error("")
                    logger.error("=" * 60)
                    logger.error("LOG_CHANNEL access failed!")
                    logger.error("")
                    logger.error("Please ensure:")
                    logger.error("1. The bot is an ADMIN in the log channel")
                    logger.error("2. The channel ID is correct")
                    logger.error("")
                    logger.error("TIP: Try using the channel USERNAME instead of ID.")
                    logger.error("")
                    logger.error("In fsb.env, change:")
                    logger.error(f"  LOG_CHANNEL={log_channel_id}")
                    logger.error("To:")
                    logger.error("  LOG_CHANNEL=@YourChannelUsername")
                    logger.error("")
                    logger.error("=" * 60)
                    logger.error("")
                    raise Exception("Please use channel username instead of ID in LOG_CHANNEL config")
        
        if log_channel:
            log_channel_peer = log_channel
            # Update config with resolved ID for future use
            Config.LOG_CHANNEL = log_channel.id
            logger.info(f"Log channel cached: {log_channel.title} (ID: {log_channel.id})")
            
            # For private channels, ensure we have proper access by fetching recent messages
            try:
                async for _ in StreamBot.get_chat_history(log_channel.id, limit=1):
                    pass
                logger.info("Log channel access verified (can read messages)")
            except Exception as hist_err:
                logger.warning(f"Could not verify channel read access: {hist_err}")
        else:
            raise Exception("Could not resolve log channel")
        
    except Exception as e:
        if "username" not in str(e).lower():
            logger.error(f"Failed to access log channel: {e}")
            logger.error("Make sure the bot is an ADMIN in the log channel!")
        raise
    
    return StreamBot


async def stop_bot():
    """Stop the bot client."""
    global StreamBot
    
    if StreamBot:
        await StreamBot.stop()
        logger.info("Bot stopped")


def get_log_channel_id():
    """Get the log channel ID."""
    return Config.LOG_CHANNEL
