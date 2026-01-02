"""
/limits command handler
"""

from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.users import get_user
from database.files import get_user_file_count, get_user_monthly_file_count, get_user_bandwidth
from utils.helpers import contains, format_bytes, format_file_size, create_progress_bar


@Client.on_message(filters.command("limits") & filters.private)
async def limits_command(client: Client, message: Message):
    """Handle /limits command."""
    user_id = message.from_user.id
    
    # Check if user is allowed
    if Config.ALLOWED_USERS and not contains(Config.ALLOWED_USERS, user_id):
        await message.reply_text("You are not allowed to use this bot.")
        return
    
    user = await get_user(user_id)
    if not user:
        await message.reply_text("❌ Failed to fetch your usage data. Please try again.")
        return
    
    # Get user's stats
    total_files = await get_user_file_count(user_id)
    monthly_files = await get_user_monthly_file_count(user_id)
    bandwidth = await get_user_bandwidth(user_id)
    
    # Calculate remaining
    remaining = max(0, Config.MONTHLY_LIMIT - monthly_files)
    
    # Calculate days until reset
    now = datetime.utcnow()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    days_until_reset = (next_month - now).days
    
    # Progress bar
    used_percent = (monthly_files / Config.MONTHLY_LIMIT) * 100 if Config.MONTHLY_LIMIT > 0 else 0
    progress_bar = create_progress_bar(used_percent, 10)
    
    max_size = format_file_size(Config.MAX_FILE_SIZE)
    
    limits_text = f"""📊 Your Usage Statistics

📁 Files:
• Total uploaded: {total_files} files
• This month: {monthly_files} / {Config.MONTHLY_LIMIT} files
• Remaining: {remaining} files

📈 Progress:
{progress_bar} {used_percent:.1f}%

📡 Bandwidth:
• Total consumed: {format_bytes(bandwidth)}

⏰ Reset:
• Days until reset: {days_until_reset} days
• Next reset: {next_month.strftime('%b %d, %Y')}

📋 Limits:
• Max file size: {max_size}
• Monthly limit: {Config.MONTHLY_LIMIT} files"""
    
    await message.reply_text(limits_text)
