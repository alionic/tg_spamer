# Telegram Account Spam Checker Bot

Telegram bot for checking multiple Telegram accounts for spam restrictions using @SpamBot. The bot processes RAR archives containing Telegram session files and their corresponding JSON configurations.

[EN]

## Features

- Process RAR archives with multiple Telegram accounts
- Check accounts for spam restrictions via @SpamBot

## Prerequisites

- Docker and Docker Compose
- Bot token from [@BotFather](https://t.me/BotFather)
- SOCKS5 proxies list
- Append NO_SPAM_PHRASES in config.py if need

## Installation

### Using Docker (Recommended)

1. Clone the repository:

```bash
git clone <repository-url>
cd tg-spamer
```

2. Create `.env` file with your bot token:

```env
BOT_TOKEN=your_bot_token
```

3. Create `proxies.txt` with your SOCKS5 proxies (one per line):

```
host:port:username:password
```

4. Start the bot with a single command:

```bash
docker-compose up -d
```

5. View logs:

```bash
docker-compose logs -f
```

## Usage

1. Start the bot:

```bash
# With Docker
docker-compose up -d

# Manual run
python bot.py
```

2. Send a RAR archive to the bot containing:
   - `.session` files (Telethon session files)
   - `.json` configuration files with matching names

### JSON Configuration Format

```json
,{
    "app_id": "your_api_id",
    "app_hash": "your_api_hash",
    "phone": "phone_number",
    "twoFA": "optional_2fa_password",
    "sdk": "system_version",
    "device": "device_model",
    "app_version": "app_version",
    "lang_pack": "language_code",
    "system_lang_pack": "system_language_code",
    ...
}
```

## Directory Structure

- `bot.py` - Main bot file (aiogram)
- `telethon_bot.py` - Telethon account checker
- `config.py` - Configuration settings
- `Dockerfile` - Docker configuration
- `docker-compose.yml` - Docker Compose configuration
- `files/`
  - `uploads/` - Temporary storage for uploaded archives
  - `extracted/` - Extracted account files
  - `new_sessions/` - New session files
