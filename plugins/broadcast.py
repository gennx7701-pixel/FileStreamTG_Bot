"""
/broadcast command handler
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
from database.users import get_all_users, delete_user
from database.broadcasts import create_broadcast, update_broadcast_progress, complete_broadcast
from utils.helpers import is_admin
from utils.logger import logger

# Broadcast state
is_broadcasting = False
broadcast_lock = asyncio.Lock()


@Client.on_message(filters.command("broadcast") & filters.private & filters.reply)
async def broadcast_command(client: Client, message: Message):
    """Handle /broadcast command (must be a reply)."""
    global is_broadcasting
    
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    # Check if already broadcasting
    async with broadcast_lock:
        if is_broadcasting:
            await message.reply_text("⚠️ A broadcast is already in progress. Please wait for it to complete.")
            return
        is_broadcasting = True
    
    try:
        # Parse options
        args = message.text.split()[1:] if message.text else []
        should_pin = "pin" in [arg.lower() for arg in args]
        
        reply_msg = message.reply_to_message
        
        pin_text = " and pin" if should_pin else ""
        await message.reply_text(f"📢 Broadcast Started\n\nStarting to send{pin_text} message to all users...\nYou will receive a summary when complete.")
        
        # Start broadcast
        await do_broadcast(client, message, reply_msg, should_pin)
        
    finally:
        is_broadcasting = False


@Client.on_message(filters.command("broadcast") & filters.private & ~filters.reply)
async def broadcast_usage(client: Client, message: Message):
    """Show broadcast usage when not replying."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    await message.reply_text(
        "❌ Usage: Reply to a message with /broadcast\n\n"
        "Options:\n"
        "• /broadcast - Send message to all users\n"
        "• /broadcast pin - Send and pin message to all users\n\n"
        "Supported:\n"
        "• Text with Telegram formatting\n"
        "• Photos, videos, documents\n"
        "• Will remove blocked/deleted users"
    )


async def do_broadcast(client: Client, message: Message, broadcast_msg: Message, should_pin: bool):
    """Perform the broadcast."""
    admin_id = message.from_user.id
    
    users = await get_all_users()
    
    if not users:
        await client.send_message(admin_id, "No users to broadcast to.")
        return
    
    # Create broadcast record
    broadcast = await create_broadcast(
        message_id=broadcast_msg.id,
        sent_by=admin_id,
        total_users=len(users),
        should_pin=should_pin
    )
    
    success_count = 0
    failed_count = 0
    blocked_count = 0
    blocked_users = []
    
    for user in users:
        target_user_id = user["user_id"]
        
        if target_user_id == admin_id:
            success_count += 1
            continue
        
        try:
            # Copy the message
            sent = await broadcast_msg.copy(chat_id=target_user_id)
            
            # Pin if required
            if should_pin:
                try:
                    await client.pin_chat_message(target_user_id, sent.id, disable_notification=True)
                except:
                    pass
            
            success_count += 1
            
        except FloodWait as e:
            await asyncio.sleep(e.value)
            # Retry
            try:
                await broadcast_msg.copy(chat_id=target_user_id)
                success_count += 1
            except:
                failed_count += 1
                
        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
            blocked_count += 1
            blocked_users.append(target_user_id)
            
        except Exception as e:
            logger.error(f"Broadcast failed for user {target_user_id}: {e}")
            failed_count += 1
        
        # Rate limit
        await asyncio.sleep(0.035)
        
        # Update progress every 100 users
        if (success_count + failed_count + blocked_count) % 100 == 0 and broadcast:
            await update_broadcast_progress(broadcast["_id"], success_count, failed_count, blocked_count)
    
    # Delete blocked users
    deleted_count = 0
    for blocked_user_id in blocked_users:
        try:
            await delete_user(blocked_user_id)
            deleted_count += 1
        except:
            pass
    
    # Complete broadcast
    if broadcast:
        await update_broadcast_progress(broadcast["_id"], success_count, failed_count, blocked_count)
        await complete_broadcast(broadcast["_id"])
    
    # Send summary
    summary = f"""✅ Broadcast Complete

📊 Summary:
━━━━━━━━━━━━━━━━
👥 Total Users: {len(users)}
✅ Successful: {success_count}
❌ Failed: {failed_count}
🚫 Blocked/Deleted: {blocked_count}
━━━━━━━━━━━━━━━━

🗑 Blocked/deleted users have been removed from the database."""
    
    await client.send_message(admin_id, summary)
