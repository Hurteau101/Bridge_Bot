# Bridge Bot

A Discord bot that integrates with the QuickPick API. Built for a client to automatically generate QuickPick links from bet slip images and post them into the corresponding Discord thread.

## Overview

The bot acts as a bridge between Discord and the QuickPick API. Users start a thread in a designated Discord channel with a bet slip image attached, and the bot passes that thread's data (the text and image) to the QuickPick API, waits for the generated link, and posts it back into the same thread. No manual steps required.


## Tech Stack

- **Language:** Python


## Getting Started

### Prerequisites

- Python 3.10+
- A Discord bot token with message content and guild intents enabled
- A QuickPick API key

### Installation

```bash
# Clone the repository
git clone https://github.com/Hurteau101/Bridge_Bot.git
cd bridge-bot

# Create a virtual environment
python -m venv venv

# Activate it
Windows - venv\Scripts\activate | Linux - venv/bin/activate

```

### Environment Variables

Create a `.env` file in the project root:

```
BOT_TOKEN=your_discord_bot_token
API_KEY=your_quickpick_api_key
ALLOWED_CHANNEL_IDS=123456789,987654321
ERROR_BOT_WEBHOOK=https://discord.com/api/webhooks/...
```

### Running the Bot

```bash
python bot.py
```

## How It Works

1. A user creates a thread (with an image attached or text of the bet) in an allowed channel
2. The bot sends the thread's text and image URLs to QuickPick's `create` endpoint
3. It polls the `status` endpoint every few seconds until the request completes
4. The generated link is posted in the thread, and the placeholder message is removed
5. Any failures are logged to an error-monitoring webhook with the relevant context

