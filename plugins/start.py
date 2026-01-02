"""
/start command handler
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database.users import get_or_create_user
from database.bans import is_user_banned
from database.files import get_file_by_message_id
from plugins.forcesub import check_force_subscription
from utils.helpers import contains
from utils.logger import logger


@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    
    # Check if user is allowed
    if Config.ALLOWED_USERS and not contains(Config.ALLOWED_USERS, user_id):
        await message.reply_text("You are not allowed to use this bot.")
        return
    
    # Check if user is banned
    is_banned, ban = await is_user_banned(user_id)
    if is_banned:
        ban_msg = f"🚫 You are banned from using this bot.\n\nReason: {ban.get('reason', 'No reason')}"
        if ban.get("expires_at"):
            ban_msg += f"\nExpires: {ban['expires_at'].strftime('%b %d, %Y %H:%M')}"
        else:
            ban_msg += "\nDuration: Permanent"
        await message.reply_text(ban_msg)
        return
    
    # Register/update user
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    await get_or_create_user(user_id, username, first_name, last_name)
    
    # Check for deep link (file_{messageID})
    if len(message.command) >= 2:
        param = message.command[1]
        
        if param.startswith("file_"):
            # Check force subscription before forwarding
            if not await check_force_subscription(client, message, user_id):
                return
            
            try:
                message_id = int(param.replace("file_", ""))
                await forward_file_to_user(client, message, user_id, message_id)
                return
            except ValueError:
                pass
    
    # Check force subscription for normal /start
    if not await check_force_subscription(client, message, user_id):
        return
    
    welcome_text = """👋 Welcome to File Stream Bot!

Send me any file and I'll generate a direct streamable link for it.

✨ Features:
• Stream videos directly in browser
• Download files at high speed
• Permanent links (as long as file exists)
• Multi-worker support for speed

📋 Commands:
• /help - How to use this bot
• /myfiles - View your uploaded files
• /limits - Check your usage limits
• /about - Bot information
• /support - Contact support

Just send me a file to get started! 📁"""
    
    await message.reply_text(welcome_text)


async def forward_file_to_user(client: Client, message: Message, user_id: int, message_id: int):
    """Forward a file from log channel to user."""
    
    # Check if file exists and is not revoked
    file = await get_file_by_message_id(message_id)
    if not file:
        await message.reply_text("❌ File not found or has been deleted.")
        return
    
    if file.get("is_revoked"):
        await message.reply_text("❌ This file link has been revoked.")
        return
    
    try:
        # Copy the message from log channel to user
        await client.copy_message(
            chat_id=user_id,
            from_chat_id=Config.LOG_CHANNEL,
            message_id=message_id
        )
        
        # Build links
        download_link = f"{Config.HOST}/dl/{message_id}?hash={file['short_hash']}&d=true"
        player_link = f"{Config.HOST}/player/{message_id}?hash={file['short_hash']}"
        
        # Create buttons
        buttons = [
            [InlineKeyboardButton("⬇️ Download", url=download_link)]
        ]
        
        if "video" in file.get("mime_type", "") or "audio" in file.get("mime_type", ""):
            buttons[0].append(InlineKeyboardButton("🎬 Watch", url=player_link))
        
        text = f"📁 {file['file_name']}\n\n⬆️ File sent above!"
        
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        logger.error(f"Failed to forward file {message_id} to user {user_id}: {e}")
        await message.reply_text("❌ Failed to send the file. Please try again.")
