"""
/myfiles command handler with callback handlers for file management
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database.users import get_or_create_user
from database.files import get_user_active_files, get_file_by_message_id, revoke_file
from plugins.forcesub import check_force_subscription, check_force_sub_callback
from utils.helpers import contains, format_bytes, truncate_string
from utils.logger import logger

FILES_PER_PAGE = 10
MAX_FILES_TO_SHOW = 40


@Client.on_message(filters.command("myfiles") & filters.private)
async def myfiles_command(client: Client, message: Message):
    """Handle /myfiles command."""
    user_id = message.from_user.id
    
    # Check if user is allowed
    if Config.ALLOWED_USERS and not contains(Config.ALLOWED_USERS, user_id):
        await message.reply_text("You are not allowed to use this bot.")
        return
    
    # Check force subscription
    if not await check_force_subscription(client, message, user_id):
        return
    
    # Register user if not exists
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    await get_or_create_user(user_id, username, first_name, last_name)
    
    await send_files_page(client, message, user_id, 1, is_callback=False)


async def send_files_page(client, message_or_query, user_id: int, page: int, is_callback: bool = False, message_id: int = 0):
    """Send paginated file list."""
    
    files, total = await get_user_active_files(user_id, page, FILES_PER_PAGE, MAX_FILES_TO_SHOW)
    
    if total == 0:
        text = "📂 Your Files\n\nYou haven't uploaded any files yet.\n\nSend me a file to get started!"
        if is_callback:
            await message_or_query.answer("No files found")
        else:
            await message_or_query.reply_text(text)
        return
    
    # Cap at max files
    display_total = min(total, MAX_FILES_TO_SHOW)
    total_pages = (display_total + FILES_PER_PAGE - 1) // FILES_PER_PAGE
    
    text = f"📂 Your Files (Page {page}/{total_pages})\nShowing {display_total} files\n\nClick a file to view details:"
    
    # Create file buttons
    buttons = []
    for i, file in enumerate(files):
        file_num = (page - 1) * FILES_PER_PAGE + i + 1
        display_name = truncate_string(file["file_name"], 30)
        
        buttons.append([
            InlineKeyboardButton(
                f"{file_num}. 📄 {display_name}",
                callback_data=f"viewfile:{user_id}:{file['message_id']}"
            )
        ])
    
    # Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"myfiles:{user_id}:{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"myfiles:{user_id}:{page + 1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    markup = InlineKeyboardMarkup(buttons)
    
    if is_callback:
        await message_or_query.edit_message_text(text, reply_markup=markup)
        await message_or_query.answer()
    else:
        await message_or_query.reply_text(text, reply_markup=markup)


@Client.on_callback_query(filters.regex(r"^myfiles:"))
async def myfiles_pagination_callback(client: Client, callback_query: CallbackQuery):
    """Handle myfiles pagination."""
    data = callback_query.data.split(":")
    if len(data) != 3:
        return
    
    user_id = int(data[1])
    page = int(data[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This is not your file list!", show_alert=True)
        return
    
    await send_files_page(client, callback_query, user_id, page, is_callback=True)


@Client.on_callback_query(filters.regex(r"^viewfile:"))
async def view_file_callback(client: Client, callback_query: CallbackQuery):
    """Handle view file details."""
    data = callback_query.data.split(":")
    if len(data) != 3:
        return
    
    user_id = int(data[1])
    message_id = int(data[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This is not your file!", show_alert=True)
        return
    
    file = await get_file_by_message_id(message_id)
    if not file:
        await callback_query.answer("❌ File not found", show_alert=True)
        return
    
    if file.get("is_revoked"):
        await callback_query.answer("❌ This file has been deleted", show_alert=True)
        return
    
    # Build links
    player_link = f"{Config.HOST}/player/{message_id}?hash={file['short_hash']}"
    download_link = f"{Config.HOST}/dl/{message_id}?hash={file['short_hash']}&d=true"
    
    # Determine file type
    mime_type = file.get("mime_type", "")
    if "video" in mime_type:
        file_type = "Video"
    elif "audio" in mime_type:
        file_type = "Audio"
    elif "image" in mime_type:
        file_type = "Image"
    elif "document" in mime_type or "pdf" in mime_type:
        file_type = "Document"
    else:
        file_type = "File"
    
    uploaded_at = file.get("uploaded_at")
    date_str = uploaded_at.strftime("%Y-%m-%d") if uploaded_at else "Unknown"
    
    text = f"📄 File Details\n\nName: {file['file_name']}\nSize: {format_bytes(file['file_size'])}\nType: {file_type}\nCreated: {date_str}"
    
    buttons = [
        [
            InlineKeyboardButton("▶️ Stream", url=player_link),
            InlineKeyboardButton("⬇️ Download", url=download_link)
        ],
        [
            InlineKeyboardButton("📥 Get File", callback_data=f"getfile:{user_id}:{message_id}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"deletefile:{user_id}:{message_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data=f"backtofiles:{user_id}")
        ]
    ]
    
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback_query.answer()


@Client.on_callback_query(filters.regex(r"^getfile:"))
async def get_file_callback(client: Client, callback_query: CallbackQuery):
    """Handle get file (send to user)."""
    data = callback_query.data.split(":")
    if len(data) != 3:
        return
    
    user_id = int(data[1])
    message_id = int(data[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This is not your file!", show_alert=True)
        return
    
    file = await get_file_by_message_id(message_id)
    if not file or file.get("is_revoked"):
        await callback_query.answer("❌ File not found or deleted", show_alert=True)
        return
    
    try:
        await client.copy_message(
            chat_id=user_id,
            from_chat_id=Config.LOG_CHANNEL,
            message_id=message_id
        )
        await callback_query.answer("✅ File sent!")
    except Exception as e:
        logger.error(f"Failed to send file {message_id} to user {user_id}: {e}")
        await callback_query.answer(f"❌ Failed to send file: {str(e)}", show_alert=True)


@Client.on_callback_query(filters.regex(r"^deletefile:"))
async def delete_file_callback(client: Client, callback_query: CallbackQuery):
    """Handle delete file confirmation."""
    data = callback_query.data.split(":")
    if len(data) != 3:
        return
    
    user_id = int(data[1])
    message_id = int(data[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This is not your file!", show_alert=True)
        return
    
    file = await get_file_by_message_id(message_id)
    if not file:
        await callback_query.answer("❌ File not found", show_alert=True)
        return
    
    text = f"⚠️ Delete File?\n\n📄 {file['file_name']}\n\nThis will permanently invalidate the download/stream link. Are you sure?"
    
    buttons = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirmdelete:{user_id}:{message_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"viewfile:{user_id}:{message_id}")
        ]
    ]
    
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback_query.answer()


@Client.on_callback_query(filters.regex(r"^confirmdelete:"))
async def confirm_delete_callback(client: Client, callback_query: CallbackQuery):
    """Handle confirmed file deletion."""
    data = callback_query.data.split(":")
    if len(data) != 3:
        return
    
    user_id = int(data[1])
    message_id = int(data[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This is not your file!", show_alert=True)
        return
    
    try:
        await revoke_file(message_id)
        await callback_query.answer("✅ File deleted successfully!")
        
        # Go back to files list
        await send_files_page(client, callback_query, user_id, 1, is_callback=True)
    except Exception as e:
        await callback_query.answer("❌ Failed to delete file", show_alert=True)


@Client.on_callback_query(filters.regex(r"^backtofiles:"))
async def back_to_files_callback(client: Client, callback_query: CallbackQuery):
    """Handle back to files list."""
    data = callback_query.data.split(":")
    if len(data) != 2:
        return
    
    user_id = int(data[1])
    
    if callback_query.from_user.id != user_id:
        return
    
    await callback_query.answer()
    await send_files_page(client, callback_query, user_id, 1, is_callback=True)


@Client.on_callback_query(filters.regex(r"^checkjoin:"))
async def check_join_callback(client: Client, callback_query: CallbackQuery):
    """Handle check join button from force sub."""
    data = callback_query.data.split(":")
    if len(data) != 2:
        return
    
    user_id = int(data[1])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This is not for you!", show_alert=True)
        return
    
    all_joined, not_joined = await check_force_sub_callback(client, user_id)
    
    if all_joined:
        await callback_query.answer("✅ Thank you for joining! You can now use the bot.")
        try:
            await callback_query.message.delete()
        except:
            pass
    else:
        msg = "❌ You haven't joined all channels yet!\n\nPlease join: " + ", ".join(not_joined)
        await callback_query.answer(msg, show_alert=True)
