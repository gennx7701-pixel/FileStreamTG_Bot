"""
aiohttp web server for file streaming.
"""

from aiohttp import web
from config import Config
from utils.logger import logger

app: web.Application = None
runner: web.AppRunner = None


async def start_web_server():
    """Start the aiohttp web server."""
    global app, runner
    
    from web.routes.player import player_handler, download_handler, assets_handler
    
    app = web.Application()
    
    # Add routes - using player.py for everything
    app.router.add_get("/player/{message_id}", player_handler)  # Player UI page
    app.router.add_get("/dl/{message_id}", download_handler)    # Direct file download/stream
    app.router.add_get("/stream/{message_id}", download_handler) # Legacy route (backwards compat)
    app.router.add_get("/assets/{filename}", assets_handler)
    
    # Add a simple home route
    app.router.add_get("/", home_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
    
    logger.info(f"Web server started on port {Config.PORT}")
    logger.info(f"Stream URL base: {Config.HOST}")


async def stop_web_server():
    """Stop the web server."""
    global runner
    
    if runner:
        await runner.cleanup()
        logger.info("Web server stopped")


async def home_handler(request: web.Request) -> web.Response:
    """Handle home page request."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>File Stream Bot</title>
        <style>
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
                min-height: 100vh;
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }
            .container {
                text-align: center;
                padding: 40px;
            }
            h1 {
                background: linear-gradient(90deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.5rem;
            }
            p {
                color: rgba(255,255,255,0.7);
                margin: 20px 0;
            }
            a {
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: #fff;
                text-decoration: none;
                border-radius: 8px;
                margin-top: 20px;
            }
            a:hover {
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📁 File Stream Bot</h1>
            <p>A Telegram bot for streaming files directly in your browser.</p>
            <p>Send files to the bot to get streamable links!</p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")
