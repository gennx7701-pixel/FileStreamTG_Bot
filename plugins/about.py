"""
/about command handler
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from utils.helpers import contains, format_file_size


@Client.on_message(filters.command("about") & filters.private)
async def about_command(client: Client, message: Message):
    """Handle /about command."""
    user_id = message.from_user.id
    
    # Check if user is allowed
    if Config.ALLOWED_USERS and not contains(Config.ALLOWED_USERS, user_id):
        await message.reply_text("You are not allowed to use this bot.")
        return
    
    max_size = format_file_size(Config.MAX_FILE_SIZE)
    
    about_text = f"""ℹ️ About File Stream Bot

Version: {Config.BOT_VERSION}
Language: Python
Framework: Pyrogram

📁 Supported Formats:
• Videos: MP4, MKV, AVI, MOV, WebM, FLV
• Audio: MP3, FLAC, WAV, OGG, M4A, AAC
• Documents: PDF, DOC, DOCX, XLS, ZIP, RAR
• Images: JPG, PNG, GIF, WebP, BMP
• Any other file Telegram supports!

📊 Limits:
• Maximum file size: {max_size}
• Monthly upload limit: {Config.MONTHLY_LIMIT} files

✨ Features:
• Direct streaming links
• Fast download speeds
• Multi-worker support
• Persistent links

🔧 Technical:
• Host: {Config.HOST}
• Hash Length: {Config.HASH_LENGTH} characters

{Config.SUPPORT_INFO}"""
    
    await message.reply_text(about_text)
