"""
Admin commands: /admin, /stats, /workers, /processes
"""

import psutil
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.users import get_user_count, get_active_user_count
from database.files import get_total_file_count, get_total_bandwidth, get_total_stream_count
from database.bans import get_ban_count
from database.sessions import get_active_sessions, get_active_session_count
from bot.workers import get_worker_count
from utils.helpers import is_admin, format_bytes, format_duration, mask_ip

start_time = datetime.utcnow()


@Client.on_message(filters.command("admin") & filters.private)
async def admin_command(client: Client, message: Message):
    """Handle /admin command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    admin_text = """🔐 Admin Commands

📊 Statistics:
• /stats - Overall bot statistics
• /workers - Worker bot status
• /processes - Active streaming sessions

👤 User Management:
• /ban <user_id> [reason] [duration] - Ban a user
• /unban <user_id> - Unban a user
• /banlist - View all banned users

🔗 Link Management:
• /revokelink <message_id> - Invalidate a specific link

📢 Broadcasting:
• /broadcast - Send message to all users (reply to a message)
• /broadcast pin - Send and pin message to all users

🔒 Force Subscribe:
• /forcesub - Manage force subscription channels

💡 Notes:
• Duration format: 1h, 1d, 1w, 1m (hours, days, weeks, months)
• Banning a user auto-revokes their links
• Broadcasts support Telegram formatting and files"""
    
    await message.reply_text(admin_text)


@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """Handle /stats command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    # Get statistics
    total_users = await get_user_count()
    active_users = await get_active_user_count()
    total_files = await get_total_file_count()
    total_bandwidth = await get_total_bandwidth()
    total_streams = await get_total_stream_count()
    active_sessions = await get_active_session_count()
    banned_users = await get_ban_count()
    
    # System resources
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    
    uptime = datetime.utcnow() - start_time
    worker_count = get_worker_count()
    
    stats_text = f"""📊 Bot Statistics

👥 Users:
• Total users: {total_users}
• Active (30d): {active_users}
• Banned: {banned_users}

📁 Files:
• Total files: {total_files}
• Total streams: {total_streams}
• Active sessions: {active_sessions}

📡 Bandwidth:
• Total used: {format_bytes(total_bandwidth)}

🤖 Workers:
• Configured: {worker_count}

💻 System:
• Uptime: {format_duration(uptime)}
• Memory: {memory_mb:.2f} MB
• CPU Cores: {psutil.cpu_count()}

⏰ Last Updated: {datetime.utcnow().strftime('%b %d, %Y %H:%M:%S')}"""
    
    await message.reply_text(stats_text)


@Client.on_message(filters.command("workers") & filters.private)
async def workers_command(client: Client, message: Message):
    """Handle /workers command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    worker_count = len(Config.MULTI_TOKENS)
    
    text = f"🤖 Worker Bot Status\n\nTotal Workers: {worker_count}\n\n"
    
    if worker_count == 0:
        text += "No worker bots configured.\n\n"
        text += "To add workers, add MULTI_TOKEN entries in fsb.env:\n"
        text += "MULTI_TOKEN1=bot_token_here\n"
        text += "MULTI_TOKEN2=bot_token_here\n"
        text += "...\n\n"
        text += "Then restart the bot."
    else:
        text += "Workers loaded from fsb.env:\n\n"
        for i in range(worker_count):
            text += f"• Worker #{i + 1}: ✅ Configured\n"
        text += "\nWorkers are automatically used for file streaming."
    
    await message.reply_text(text)


@Client.on_message(filters.command("processes") & filters.private)
async def processes_command(client: Client, message: Message):
    """Handle /processes command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    sessions = await get_active_sessions()
    
    if not sessions:
        await message.reply_text("📡 Active Streaming Sessions\n\nNo active streaming sessions at the moment.")
        return
    
    text = f"📡 Active Streaming Sessions\n\nTotal: {len(sessions)} active sessions\n\n"
    
    # Group by IP
    ip_map = {}
    for s in sessions:
        ip = s.get("ip_address", "unknown")
        if ip not in ip_map:
            ip_map[ip] = []
        ip_map[ip].append(s)
    
    i = 1
    for ip, ip_sessions in ip_map.items():
        total_bw = sum(s.get("bytes_sent", 0) for s in ip_sessions)
        
        text += f"{i}. IP: {mask_ip(ip)}\n"
        text += f"   Sessions: {len(ip_sessions)}\n"
        text += f"   Bandwidth: {format_bytes(total_bw)}\n"
        
        if len(ip_sessions) <= 3:
            for s in ip_sessions:
                text += f"   • MsgID: {s.get('message_id', '?')}, Sent: {format_bytes(s.get('bytes_sent', 0))}\n"
        text += "\n"
        
        i += 1
        if i > 10:
            text += f"... and {len(ip_map) - 10} more IPs\n"
            break
    
    await message.reply_text(text)
