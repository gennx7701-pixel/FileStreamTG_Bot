"""
Force subscription management: /forcesub command and helper functions
"""

from typing import List, Tuple
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivate
from database.forcesub import get_forcesub_channels, add_forcesub_channel, remove_forcesub_channel
from utils.helpers import is_admin
from utils.logger import logger


@Client.on_message(filters.command("forcesub") & filters.private)
async def forcesub_command(client: Client, message: Message):
    """Handle /forcesub command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await show_forcesub_channels(message)
        return
    
    action = args[0].lower()
    
    if action == "list":
        await show_forcesub_channels(message)
        
    elif action == "add":
        if len(args) < 2:
            await message.reply_text("❌ Usage: /forcesub add @channel_username\n\nExample: /forcesub add @mychannel")
            return
        await add_forcesub(client, message, args[1])
        
    elif action in ["remove", "rm", "del"]:
        if len(args) < 2:
            await message.reply_text("❌ Usage: /forcesub remove @channel_username\n\nExample: /forcesub remove @mychannel")
            return
        await remove_forcesub(message, args[1])
        
    else:
        await message.reply_text(
            "❌ Invalid action\n\n"
            "Usage:\n"
            "• /forcesub - Show current force sub channels\n"
            "• /forcesub list - Show current force sub channels\n"
            "• /forcesub add @channel - Add a channel (max 4)\n"
            "• /forcesub remove @channel - Remove a channel\n\n"
            'Note: Bot must be admin in the channel with "Add Members" permission.'
        )


async def show_forcesub_channels(message: Message):
    """Show current force subscription channels."""
    channels = await get_forcesub_channels()
    
    if not channels:
        await message.reply_text(
            "📢 Force Subscribe Channels\n\n"
            "No channels configured.\n\n"
            "Users can use the bot without subscribing to any channel.\n\n"
            "Add a channel: /forcesub add @channel_username"
        )
        return
    
    text = f"📢 Force Subscribe Channels\n\n"
    text += f"Users must subscribe to these channels ({len(channels)}/4):\n\n"
    
    for i, ch in enumerate(channels):
        text += f"{i + 1}. {ch.get('channel_username', 'Unknown')}\n"
    
    text += "\nCommands:\n"
    text += "• /forcesub add @channel - Add channel\n"
    text += "• /forcesub remove @channel - Remove channel"
    
    await message.reply_text(text)


async def add_forcesub(client: Client, message: Message, channel_username: str):
    """Add a force subscription channel."""
    channel_username = channel_username.lstrip("@").strip()
    
    if not channel_username:
        await message.reply_text("❌ Please provide a valid channel username.")
        return
    
    channels = await get_forcesub_channels()
    
    if len(channels) >= 4:
        await message.reply_text("❌ Maximum 4 force sub channels allowed. Remove one first.")
        return
    
    # Check if already exists
    for ch in channels:
        existing = ch.get("channel_username", "").lstrip("@").lower()
        if existing == channel_username.lower():
            await message.reply_text("❌ This channel is already in the force sub list.")
            return
    
    try:
        # Resolve the channel
        chat = await client.get_chat(channel_username)
        channel_id = chat.id
        
        # Add to database
        await add_forcesub_channel(channel_id, 0, f"@{channel_username}")
        
        await message.reply_text(
            f"✅ Channel Added\n\n"
            f"@{channel_username} has been added to force subscribe list.\n\n"
            f"Users must now subscribe to this channel to use the bot."
        )
        
    except Exception as e:
        logger.error(f"Failed to add forcesub channel @{channel_username}: {e}")
        await message.reply_text(
            f"❌ Could not find channel @{channel_username}. Make sure:\n"
            "• The channel exists\n"
            "• The bot is an admin in the channel\n"
            "• The username is correct"
        )


async def remove_forcesub(message: Message, channel_username: str):
    """Remove a force subscription channel."""
    channel_username = channel_username.lstrip("@").strip()
    
    if not channel_username:
        await message.reply_text("❌ Please provide a valid channel username.")
        return
    
    success = await remove_forcesub_channel(f"@{channel_username}")
    
    if success:
        await message.reply_text(f"✅ Channel Removed\n\n@{channel_username} has been removed from force subscribe list.")
    else:
        await message.reply_text("❌ Failed to remove channel or channel not found.")


async def check_force_subscription(client: Client, message: Message, user_id: int) -> bool:
    """
    Check if user is subscribed to all force sub channels.
    Returns True if user can proceed, False if blocked.
    """
    if is_admin(user_id):
        return True
    
    channels = await get_forcesub_channels()
    if not channels:
        return True
    
    not_joined = []
    
    for ch in channels:
        username = ch.get("channel_username", "")
        
        is_member = await check_membership(client, user_id, username)
        if not is_member:
            not_joined.append(username)
    
    if not not_joined:
        return True
    
    # User hasn't joined all channels - send message
    text = "🔒 Join Required Channels\n\n"
    text += "To use this bot, you must join the following channels:\n\n"
    
    buttons = []
    for i, ch in enumerate(not_joined):
        text += f"{i + 1}. {ch}\n"
        buttons.append([
            InlineKeyboardButton(
                f"Join {ch}",
                url=f"https://t.me/{ch.lstrip('@')}"
            )
        ])
    
    text += "\nAfter joining, click the button below or send your message again."
    
    buttons.append([
        InlineKeyboardButton("✅ I've Joined", callback_data=f"checkjoin:{user_id}")
    ])
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    
    return False


async def check_force_sub_callback(client: Client, user_id: int) -> Tuple[bool, List[str]]:
    """
    Check force subscription without sending message.
    Returns (all_joined, not_joined_list)
    """
    if is_admin(user_id):
        return True, []
    
    channels = await get_forcesub_channels()
    if not channels:
        return True, []
    
    not_joined = []
    
    for ch in channels:
        username = ch.get("channel_username", "")
        is_member = await check_membership(client, user_id, username)
        if not is_member:
            not_joined.append(username)
    
    return len(not_joined) == 0, not_joined


async def check_membership(client: Client, user_id: int, channel_username: str) -> bool:
    """Check if user is a member of the channel."""
    try:
        username = channel_username.lstrip("@")
        member = await client.get_chat_member(username, user_id)
        
        # Check status
        if member.status in ["member", "administrator", "creator", "owner"]:
            return True
        return False
        
    except UserNotParticipant:
        return False
    except (ChatAdminRequired, ChannelPrivate):
        # If we can't check, assume they're a member to avoid blocking
        logger.warning(f"Cannot check membership for @{channel_username}")
        return True
    except Exception as e:
        logger.error(f"Error checking membership for user {user_id} in @{channel_username}: {e}")
        return True  # Fail open
