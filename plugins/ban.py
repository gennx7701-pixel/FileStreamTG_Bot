"""
Ban commands: /ban, /unban, /banlist
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from database.bans import ban_user, unban_user, is_user_banned, get_banned_users
from database.files import revoke_user_files
from utils.helpers import is_admin, parse_duration, format_duration


@Client.on_message(filters.command("ban") & filters.private)
async def ban_command(client: Client, message: Message):
    """Handle /ban command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("You are not authorized to use admin commands.")
        return
    
    # Parse command: /ban <user_id> [reason] [duration]
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await message.reply_text(
            "Usage: /ban <user_id> [reason] [duration]\n\n"
            "Examples:\n"
            "/ban 123456789\n"
            "/ban 123456789 Spamming\n"
            "/ban 123456789 Abuse 7d\n\n"
            "Duration: 1h, 1d, 1w, 1m or empty for permanent"
        )
        return
    
    try:
        target_user_id = int(args[0])
    except ValueError:
        await message.reply_text("Invalid user ID. Please provide a valid numeric user ID.")
        return
    
    # Parse reason and duration
    reason = "No reason provided"
    duration = None
    
    if len(args) >= 2:
        # Check if last arg is a duration
        last_arg = args[-1]
        parsed_duration = parse_duration(last_arg)
        
        if parsed_duration:
            duration = parsed_duration
            if len(args) > 2:
                reason = " ".join(args[1:-1])
        else:
            reason = " ".join(args[1:])
    
    # Ban the user
    await ban_user(target_user_id, user_id, reason, duration)
    
    # Revoke all links
    revoked_count = await revoke_user_files(target_user_id)
    
    duration_text = format_duration(duration) if duration else "Permanent"
    
    success_text = f"✅ User Banned Successfully\n\nUser ID: {target_user_id}\nReason: {reason}\nDuration: {duration_text}\nLinks Revoked: {revoked_count}"
    
    await message.reply_text(success_text)


@Client.on_message(filters.command("unban") & filters.private)
async def unban_command(client: Client, message: Message):
    """Handle /unban command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("You are not authorized to use admin commands.")
        return
    
    # Parse command: /unban <user_id>
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await message.reply_text("Usage: /unban <user_id>")
        return
    
    try:
        target_user_id = int(args[0])
    except ValueError:
        await message.reply_text("Invalid user ID. Please provide a valid numeric user ID.")
        return
    
    # Check if banned
    is_banned, _ = await is_user_banned(target_user_id)
    if not is_banned:
        await message.reply_text("This user is not currently banned.")
        return
    
    # Unban
    await unban_user(target_user_id)
    
    await message.reply_text(f"✅ User Unbanned Successfully\n\nUser ID: {target_user_id}\n\nThe user can now use the bot again.")


@Client.on_message(filters.command("banlist") & filters.private)
async def banlist_command(client: Client, message: Message):
    """Handle /banlist command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("You are not authorized to use admin commands.")
        return
    
    bans = await get_banned_users()
    
    if not bans:
        await message.reply_text("🚫 Ban List\n\nNo users are currently banned.")
        return
    
    text = f"🚫 Ban List\n\nTotal banned: {len(bans)} users\n\n"
    
    for i, ban in enumerate(bans[:20]):
        expires_text = "Permanent"
        if ban.get("expires_at"):
            expires_text = ban["expires_at"].strftime("%b %d, %Y %H:%M")
        
        text += f"{i + 1}. User ID: {ban['user_id']}\n"
        text += f"   Reason: {ban.get('reason', 'N/A')}\n"
        text += f"   Banned: {ban.get('banned_at', 'Unknown').strftime('%b %d, %Y') if ban.get('banned_at') else 'Unknown'}\n"
        text += f"   Expires: {expires_text}\n\n"
    
    if len(bans) > 20:
        text += f"... and {len(bans) - 20} more banned users"
    
    await message.reply_text(text)
