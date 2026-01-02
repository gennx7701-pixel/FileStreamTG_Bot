"""
/support command handler
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from plugins.forcesub import check_force_subscription
from utils.helpers import contains, format_file_size


@Client.on_message(filters.command("support") & filters.private)
async def support_command(client: Client, message: Message):
    """Handle /support command."""
    user_id = message.from_user.id
    
    # Check if user is allowed
    if Config.ALLOWED_USERS and not contains(Config.ALLOWED_USERS, user_id):
        await message.reply_text("You are not allowed to use this bot.")
        return
    
    # Check force subscription
    if not await check_force_subscription(client, message, user_id):
        return
    
    max_size = format_file_size(Config.MAX_FILE_SIZE)
    
    support_text = f"""📞 Support & Contact

{Config.SUPPORT_INFO}

🐛 Report Issues:
When reporting issues, please include:
• What you were trying to do
• The error message (if any)
• The file type and size
• Your user ID: {user_id}

❓ Common Issues:

Q: Link not working?
A: The file might have been deleted or the link revoked.

Q: Slow streaming?
A: Try using the download link instead, or check your internet connection.

Q: File too large?
A: Maximum file size is {max_size}

Q: Upload limit reached?
A: Use /limits to check your current usage. Limits reset monthly."""
    
    await message.reply_text(support_text)
