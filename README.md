# Telegram File Stream Bot 🚀

<p align="center">
  <b>A powerful Telegram bot to generate direct download/stream links for your Telegram files</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/pyrogram-2.0+-green.svg" alt="Pyrogram">
  <img src="https://img.shields.io/badge/mongodb-supported-brightgreen.svg" alt="MongoDB">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
</p>

---

## ✨ Features

- 📁 **File Streaming** - Generate direct streamable links for any Telegram file
- 🎬 **Web Player** - Built-in video player with advanced controls
- 📱 **Mobile Friendly** - Responsive design works on all devices
- 🔗 **External Players** - Open in MX Player, VLC, KM Player
- 📊 **User Management** - Track uploads, bandwidth, and usage limits
- 🚫 **Ban System** - Ban/unban users with reasons and expiry
- 📢 **Broadcast** - Send messages to all users with pinning support
- 🔐 **Force Subscribe** - Require users to join channels before using
- 👥 **Multi-Worker** - Use multiple bots to speed up streaming
- 💾 **MongoDB** - Persistent storage for users, files, and settings

---

## 📋 Requirements

- Python 3.10 or higher
- MongoDB database
- Telegram API credentials

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/suryapaul01/FileStreamTG_Bot.git
cd FileStreamTG_Bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp fsb.env.sample fsb.env
nano fsb.env  # Edit with your values
```

### 4. Run the bot

```bash
python bot.py
```

---

## ⚙️ Configuration

Create a `fsb.env` file with the following variables:

### Required Variables

| Variable | Description |
|----------|-------------|
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `LOG_CHANNEL` | Channel ID where bot stores files (bot must be admin) |
| `MONGODB_URI` | MongoDB connection string |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | Web server port |
| `DATABASE_NAME` | filestream_bot | MongoDB database name |
| `ADMIN_USERS` | - | Comma-separated admin user IDs |
| `HASH_LENGTH` | 6 | URL hash length (5-32) |
| `MAX_FILE_SIZE` | 2GB | Maximum file size in bytes |
| `MONTHLY_LIMIT` | 100 | Monthly upload limit per user |
| `FORCE_SUB_CHANNELS` | - | Channels users must join |
| `SUPPORT_INFO` | - | Support contact info |
| `HOST` | auto | Server URL for links |

### Multi-Worker Setup

Add multiple bot tokens to speed up streaming:

```env
MULTI_TOKEN1=your_worker_bot_token_1
MULTI_TOKEN2=your_worker_bot_token_2
MULTI_TOKEN3=your_worker_bot_token_3
```

> ⚠️ **Important:** All worker bots must be admins in the LOG_CHANNEL!

---

## 🤖 Bot Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Display bot features and usage |
| `/myfiles` | List all your uploaded files |
| `/limits` | View your usage limits and quota |
| `/about` | Bot information and version |
| `/support` | Contact admin or report issues |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Show all admin commands |
| `/stats` | Overall bot statistics |
| `/workers` | Worker bot status |
| `/processes` | Active streaming sessions |
| `/ban <user_id> [reason] [duration]` | Ban a user |
| `/unban <user_id>` | Unban a user |
| `/banlist` | View all banned users |
| `/revokelink <message_id>` | Invalidate a specific link |
| `/broadcast` | Send message to all users |
| `/forcesub add <@channel>` | Add force subscribe channel |
| `/forcesub remove <@channel>` | Remove force subscribe channel |

---

## 📁 Project Structure

```
FileStreamTG_Bot/
├── bot.py              # Main entry point
├── config.py           # Configuration loader
├── requirements.txt    # Python dependencies
├── fsb.env.sample      # Sample environment file
├── bot/
│   ├── client.py       # Main Pyrogram client
│   └── workers.py      # Multi-worker management
├── plugins/
│   ├── start.py        # /start command
│   ├── stream.py       # File upload handler
│   ├── myfiles.py      # User files management
│   ├── admin.py        # Admin commands
│   ├── ban.py          # Ban system
│   ├── broadcast.py    # Broadcast feature
│   └── ...
├── database/
│   ├── users.py        # User database operations
│   ├── files.py        # File database operations
│   ├── bans.py         # Ban database operations
│   └── ...
├── web/
│   ├── server.py       # aiohttp web server
│   ├── routes/
│   │   └── player.py   # Stream & player routes
│   └── templates/
│       └── player.html # Video player template
└── utils/
    ├── file_properties.py
    ├── hashing.py
    ├── helpers.py
    └── logger.py
```

---

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

```bash
docker build -t filestream-bot .
docker run -d --env-file fsb.env -p 8080:8080 filestream-bot
```

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Credits

- [Pyrogram](https://github.com/pyrogram/pyrogram) - Telegram MTProto API framework
- [aiohttp](https://github.com/aio-libs/aiohttp) - Async HTTP server
- [Motor](https://github.com/mongodb/motor) - Async MongoDB driver

---

## 📧 Support

For support, contact [@tataa_sumo](https://t.me/tataa_sumo) on Telegram.

