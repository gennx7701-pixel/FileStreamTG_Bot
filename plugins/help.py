"""
/help command handler
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from utils.helpers import contains, format_file_size


@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Handle /help command."""
    user_id = message.from_user.id
    
    # Check if user is allowed
    if Config.ALLOWED_USERS and not contains(Config.ALLOWED_USERS, user_id):
        await message.reply_text("You are not allowed to use this bot.")
        return
    
    max_size = format_file_size(Config.MAX_FILE_SIZE)
    
    help_text = f"""🤖 File Stream Bot - Help

📤 How to Use:
Simply send me any file and I'll generate a direct streamable link for it!

📁 Supported File Types:
• Videos (MP4, MKV, AVI, etc.)
• Audio (MP3, FLAC, OGG, etc.)
• Documents (PDF, DOC, ZIP, etc.)
• Photos (JPG, PNG, GIF, etc.)
• Any other file type!

🔗 Generated Links:
• Stream Link - Play media directly in browser
• Download Link - Direct download the file

📋 Available Commands:
• /start - Start the bot
• /help - Show this help message
• /myfiles - View your uploaded files
• /limits - Check your usage limits
• /about - Bot information
• /support - Contact support

💡 Tips:
• Maximum file size: {max_size}
• Links remain active as long as the file exists
• Videos and audio can be streamed directly
• Use download links for faster downloads"""
    
    await message.reply_text(help_text)
