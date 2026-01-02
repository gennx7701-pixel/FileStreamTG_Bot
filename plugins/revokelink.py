"""
/revokelink command handler
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from database.files import get_file_by_message_id, revoke_file
from utils.helpers import is_admin


@Client.on_message(filters.command("revokelink") & filters.private)
async def revokelink_command(client: Client, message: Message):
    """Handle /revokelink command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    # Parse command: /revokelink <message_id>
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await message.reply_text(
            "❌ **Usage:** /revokelink <message_id>\n\n"
            "**Example:**\n"
            "• /revokelink 12345\n\n"
            "The message_id is the ID of the message in the log channel.\n"
            "You can find it in the stream URL: /stream/<message_id>?hash=..."
        )
        return
    
    try:
        message_id = int(args[0])
    except ValueError:
        await message.reply_text("❌ Invalid message ID. Please provide a valid numeric message ID.")
        return
    
    # Check if file exists
    file = await get_file_by_message_id(message_id)
    if not file:
        await message.reply_text("❌ File not found with this message ID.")
        return
    
    if file.get("is_revoked"):
        await message.reply_text("ℹ️ This link is already revoked.")
        return
    
    # Revoke the file
    await revoke_file(message_id)
    
    await message.reply_text(
        f"✅ **Link Revoked Successfully**\n\n"
        f"**Message ID:** {message_id}\n"
        f"**File Name:** {file.get('file_name', 'Unknown')}\n"
        f"**Uploaded By:** {file.get('user_id', 'Unknown')}\n\n"
        f"The link will no longer work for streaming or downloading."
    )
