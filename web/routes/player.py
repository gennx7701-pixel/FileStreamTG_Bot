"""
Player route handler for video player page and file streaming.
Combined handler - serves both player UI and file downloads.
"""

import os
import uuid
from aiohttp import web
from jinja2 import Template
from pyrogram.errors import FileReferenceExpired, FileReferenceInvalid
from config import Config
from bot.workers import get_main_bot
from bot.client import bot_username
from database.files import get_file_by_message_id, is_file_revoked, update_file_access
from database.sessions import create_session, update_session, end_session
from database.users import update_user_bandwidth
from utils.hashing import pack_file, check_hash
from utils.file_properties import get_file_properties, get_file_id
from utils.helpers import format_bytes, extract_telegram_link, extract_username
from utils.logger import logger

# Chunk size for streaming (1MB)
CHUNK_SIZE = 1024 * 1024

# Player HTML template
PLAYER_TEMPLATE = None


def get_player_template() -> str:
    """Load player template."""
    global PLAYER_TEMPLATE
    if PLAYER_TEMPLATE is None:
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "player.html")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                PLAYER_TEMPLATE = f.read()
        else:
            PLAYER_TEMPLATE = get_fallback_template()
    return PLAYER_TEMPLATE


async def player_handler(request: web.Request) -> web.Response:
    """Handle player page request - shows the video/audio player UI."""
    
    # Get message ID
    try:
        message_id = int(request.match_info["message_id"])
    except ValueError:
        return web.Response(status=400, text="Invalid message ID")
    
    # Get hash parameter
    auth_hash = request.query.get("hash", "")
    if not auth_hash:
        return web.Response(status=400, text="Missing hash parameter")
    
    # Check if download is requested - redirect to download handler
    if request.query.get("d") == "true":
        return await download_handler(request)
    
    # Use main bot for message retrieval (it has the peer cached reliably)
    main_bot = get_main_bot()
    if not main_bot:
        return web.Response(status=503, text="Bot not available")
    
    try:
        # Get the message using main bot
        message = await main_bot.get_messages(Config.LOG_CHANNEL, message_id)
        
        if not message or not message.media:
            return web.Response(status=404, text="File not found")
        
        # Get file properties
        props = get_file_properties(message)
        
        # Verify hash
        expected_hash = pack_file(
            props["file_name"],
            props["file_size"],
            props["mime_type"],
            props["file_id_num"]
        )
        
        if not check_hash(auth_hash, expected_hash):
            return web.Response(status=400, text="Invalid hash")
        
        # Build URLs - all using /player/ now
        stream_url = f"{Config.HOST}/dl/{message_id}?hash={auth_hash}"
        download_url = f"{Config.HOST}/dl/{message_id}?hash={auth_hash}&d=true"
        
        # Stream URL without protocol for intent:// links
        stream_url_no_protocol = stream_url.replace("http://", "").replace("https://", "")
        
        # Bot URL
        bot_name = bot_username or "FileStreamBot"
        telegram_bot_url = f"https://t.me/{bot_name}?start=file_{message_id}"
        
        # Support URL
        support_url = extract_telegram_link(Config.SUPPORT_INFO)
        if not support_url:
            username = extract_username(Config.SUPPORT_INFO)
            support_url = f"https://t.me/{username}" if username else "https://t.me/EverythingSuckz"
        
        # Template data
        data = {
            "FileName": props["file_name"],
            "FileSize": format_bytes(props["file_size"]),
            "MimeType": props["mime_type"],
            "StreamURL": stream_url,
            "StreamURLNoProtocol": stream_url_no_protocol,
            "DownloadURL": download_url,
            "TelegramBotURL": telegram_bot_url,
            "SupportURL": support_url,
            "MessageID": message_id,
            "Hash": auth_hash
        }
        
        # Render template
        template = Template(get_player_template())
        html = template.render(**data)
        
        return web.Response(text=html, content_type="text/html", charset="utf-8")
        
    except Exception as e:
        logger.error(f"Player error for message {message_id}: {e}")
        return web.Response(status=500, text=f"Error: {str(e)}")


async def download_handler(request: web.Request) -> web.StreamResponse:
    """Handle file streaming/download requests."""
    
    # Get message ID
    try:
        message_id = int(request.match_info["message_id"])
    except ValueError:
        return web.Response(status=400, text="Invalid message ID")
    
    # Get hash parameter
    auth_hash = request.query.get("hash", "")
    if not auth_hash:
        return web.Response(status=400, text="Missing hash parameter")
    
    # Check if file is revoked
    revoked = await is_file_revoked(message_id)
    if revoked:
        return web.Response(status=403, text="This link has been revoked")
    
    # Use main bot to get the message (it has the peer cached reliably)
    main_bot = get_main_bot()
    if not main_bot:
        return web.Response(status=503, text="Bot not available")
    
    try:
        # Get the message from Telegram using main bot
        message = await main_bot.get_messages(Config.LOG_CHANNEL, message_id)
        
        if not message or not message.media:
            return web.Response(status=404, text="File not found")
        
        # Get file properties
        props = get_file_properties(message)
        
        # Verify hash
        expected_hash = pack_file(
            props["file_name"],
            props["file_size"],
            props["mime_type"],
            props["file_id_num"]
        )
        
        if not check_hash(auth_hash, expected_hash):
            return web.Response(status=400, text="Invalid hash")
        
        # Get file owner for bandwidth tracking
        db_file = await get_file_by_message_id(message_id)
        file_owner_id = db_file.get("user_id", 0) if db_file else 0
        
        # Create session
        session_id = str(uuid.uuid4())
        client_ip = request.remote or "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        await create_session(session_id, message_id, file_owner_id, client_ip, user_agent)
        
        file_size = props["file_size"]
        file_name = props["file_name"]
        mime_type = props["mime_type"] or "application/octet-stream"
        
        # Handle range requests
        range_header = request.headers.get("Range", "")
        
        if range_header:
            # Parse range header
            try:
                range_spec = range_header.replace("bytes=", "")
                start_str, end_str = range_spec.split("-")
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
            except:
                start = 0
                end = file_size - 1
            
            # Ensure valid range
            if start >= file_size:
                return web.Response(status=416, text="Range not satisfiable")
            end = min(end, file_size - 1)
            
            content_length = end - start + 1
            
            response = web.StreamResponse(
                status=206,
                headers={
                    "Content-Type": mime_type,
                    "Content-Length": str(content_length),
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": get_content_disposition(request, file_name)
                }
            )
        else:
            start = 0
            end = file_size - 1
            content_length = file_size
            
            response = web.StreamResponse(
                status=200,
                headers={
                    "Content-Type": mime_type,
                    "Content-Length": str(content_length),
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": get_content_disposition(request, file_name)
                }
            )
        
        await response.prepare(request)
        
        # Stream the file
        if request.method != "HEAD":
            bytes_sent = 0
            
            try:
                # Always use main bot for streaming (workers may not have channel access)
                # Fetch fresh message to avoid FILE_REFERENCE_EXPIRED
                async for chunk in stream_file_chunks(main_bot, message_id, start, end):
                    await response.write(chunk)
                    bytes_sent += len(chunk)
                
            except ConnectionResetError:
                logger.debug(f"Client disconnected while streaming file {message_id}")
            except Exception as e:
                logger.error(f"Error streaming file {message_id}: {e}")
            
            finally:
                # Update stats
                await update_session(session_id, bytes_sent)
                await end_session(session_id)
                await update_file_access(message_id, bytes_sent)
                if file_owner_id:
                    await update_user_bandwidth(file_owner_id, bytes_sent)
        
        await response.write_eof()
        return response
        
    except Exception as e:
        logger.error(f"Download error for message {message_id}: {e}")
        return web.Response(status=500, text=f"Error: {str(e)}")


async def stream_file_chunks(client, message_id: int, start: int, end: int):
    """
    Stream file in chunks using Pyrogram's download functionality.
    Yields chunks of data between start and end bytes.
    Always fetches fresh message to avoid FILE_REFERENCE_EXPIRED.
    """
    # Calculate the offset in MB (Pyrogram's stream_media uses offset as chunk number)
    offset_mb = start // CHUNK_SIZE
    bytes_to_skip = start % CHUNK_SIZE
    bytes_remaining = end - start + 1
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Always fetch fresh message to get valid file reference
            message = await client.get_messages(Config.LOG_CHANNEL, message_id)
            if not message or not message.media:
                raise Exception("Message not found or has no media")
            
            file_id = get_file_id(message)
            if not file_id:
                raise Exception("Could not get file ID from message")
            
            # Reset counters for each attempt
            current_bytes_to_skip = bytes_to_skip
            current_bytes_remaining = bytes_remaining
            
            # Pyrogram's stream_media returns an async generator that yields chunks
            async for chunk in client.stream_media(message, offset=offset_mb):
                if current_bytes_remaining <= 0:
                    break
                    
                chunk_data = bytes(chunk)
                
                # Skip bytes if needed (for range requests that don't start at chunk boundary)
                if current_bytes_to_skip > 0:
                    skip_amount = min(current_bytes_to_skip, len(chunk_data))
                    chunk_data = chunk_data[skip_amount:]
                    current_bytes_to_skip -= skip_amount
                
                if len(chunk_data) == 0:
                    continue
                    
                # Trim chunk if we've reached the end
                if len(chunk_data) > current_bytes_remaining:
                    chunk_data = chunk_data[:current_bytes_remaining]
                
                current_bytes_remaining -= len(chunk_data)
                yield chunk_data
            
            # If we get here without error, we're done
            return
            
        except (FileReferenceExpired, FileReferenceInvalid) as e:
            if attempt < max_retries - 1:
                logger.warning(f"File reference expired, retrying (attempt {attempt + 2}/{max_retries})")
                continue
            else:
                logger.error(f"File reference expired after {max_retries} attempts: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in stream_file_chunks (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                continue
            raise


def get_content_disposition(request: web.Request, file_name: str) -> str:
    """Get Content-Disposition header value."""
    # Check if download is requested
    if request.query.get("d") == "true":
        disposition = "attachment"
    else:
        disposition = "inline"
    
    # Escape filename for header
    safe_name = file_name.replace('"', '\\"')
    return f'{disposition}; filename="{safe_name}"'


async def assets_handler(request: web.Request) -> web.Response:
    """Serve static assets."""
    filename = request.match_info["filename"]
    
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "images")
    file_path = os.path.join(static_dir, filename)
    
    if not os.path.exists(file_path):
        return web.Response(status=404, text="Asset not found")
    
    # Determine content type
    content_type = "application/octet-stream"
    if filename.endswith(".png"):
        content_type = "image/png"
    elif filename.endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    elif filename.endswith(".svg"):
        content_type = "image/svg+xml"
    elif filename.endswith(".gif"):
        content_type = "image/gif"
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    return web.Response(body=data, content_type=content_type)


def get_fallback_template() -> str:
    """Fallback minimal player template if main template is missing."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ FileName }} - File Stream Player</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container { max-width: 900px; width: 100%; }
        h1 { color: #667eea; margin-bottom: 20px; word-break: break-all; }
        video, audio {
            width: 100%;
            max-height: 70vh;
            background: #000;
            border-radius: 16px;
            margin-bottom: 20px;
        }
        .info { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        .buttons { display: flex; gap: 10px; flex-wrap: wrap; }
        .btn {
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s;
        }
        .primary { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; }
        .secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }
        .btn:hover { transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="container">
        <video controls autoplay>
            <source src="{{ StreamURL }}" type="{{ MimeType }}">
            Your browser does not support video playback.
        </video>
        <div class="info">
            <h2>{{ FileName }}</h2>
            <p>Size: {{ FileSize }}</p>
        </div>
        <div class="buttons">
            <a href="{{ DownloadURL }}" class="btn primary">⬇️ Download</a>
            <a href="{{ TelegramBotURL }}" class="btn secondary">📱 Get in Telegram</a>
        </div>
    </div>
</body>
</html>'''
