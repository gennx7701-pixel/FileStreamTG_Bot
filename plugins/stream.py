"""
File stream handler - generates stream links for uploaded files
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database.users import get_or_create_user, update_user_stats
from database.bans import is_user_banned
from database.files import create_file, get_user_monthly_file_count
from plugins.forcesub import check_force_subscription
from utils.helpers import contains
from utils.hashing import pack_file, get_short_hash
from utils.file_properties import get_file_properties, is_supported_media
from utils.logger import logger


@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo | filters.voice | filters.video_note | filters.animation))
async def handle_file(client: Client, message: Message):
    """Handle any media file and generate stream link."""
    user_id = message.from_user.id
    
    # Check if user is allowed
    if Config.ALLOWED_USERS and not contains(Config.ALLOWED_USERS, user_id):
        await message.reply_text("You are not allowed to use this bot.")
        return
    
    # Check force subscription
    if not await check_force_subscription(client, message, user_id):
        return
    
    # Check if user is banned
    is_banned, ban = await is_user_banned(user_id)
    if is_banned:
        ban_msg = f"🚫 You are banned from using this bot.\n\nReason: {ban.get('reason', 'No reason')}"
        if ban.get("expires_at"):
            ban_msg += f"\nExpires: {ban['expires_at'].strftime('%b %d, %Y %H:%M')}"
        await message.reply_text(ban_msg)
        return
    
    # Check monthly limit
    monthly_files = await get_user_monthly_file_count(user_id)
    if monthly_files >= Config.MONTHLY_LIMIT:
        await message.reply_text(
            f"⚠️ Monthly Upload Limit Reached\n\n"
            f"You've uploaded {monthly_files} files this month.\n"
            f"Limit: {Config.MONTHLY_LIMIT} files/month\n\n"
            f"Use /limits to check when your limit resets."
        )
        return
    
    # Check if media is supported
    if not is_supported_media(message):
        await message.reply_text("Sorry, this message type is unsupported.")
        return
    
    try:
        # Forward to log channel
        forwarded = await message.forward(Config.LOG_CHANNEL)
        
        # Get file properties
        props = get_file_properties(forwarded)
        
        # Generate hash
        full_hash = pack_file(
            props["file_name"],
            props["file_size"],
            props["mime_type"],
            props["file_id_num"]
        )
        short_hash = get_short_hash(full_hash)
        
        # Generate links
        stream_link = f"{Config.HOST}/dl/{forwarded.id}?hash={short_hash}"
        player_link = f"{Config.HOST}/player/{forwarded.id}?hash={short_hash}"
        download_link = f"{stream_link}&d=true"
        
        # Save to database
        file_data = {
            "message_id": forwarded.id,
            "user_id": user_id,
            "file_name": props["file_name"],
            "file_size": props["file_size"],
            "mime_type": props["mime_type"],
            "file_hash": full_hash,
            "short_hash": short_hash,
            "stream_link": stream_link
        }
        
        await create_file(file_data)
        
        # Update user stats
        await update_user_stats(user_id)
        
        # Create buttons
        buttons = [
            [InlineKeyboardButton("⬇️ Download", url=download_link)]
        ]
        
        # Add watch button for video/audio
        if "video" in props["mime_type"] or "audio" in props["mime_type"]:
            buttons[0].append(InlineKeyboardButton("🎬 Watch", url=player_link))
        
        # Reply with link
        markup = InlineKeyboardMarkup(buttons) if "localhost" not in stream_link else None
        
        await message.reply_text(
            f"`{player_link}`",
            reply_markup=markup,
            reply_to_message_id=message.id
        )
        
    except Exception as e:
        logger.error(f"Error processing file from user {user_id}: {e}")
        await message.reply_text(f"Error - {str(e)}")
