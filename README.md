# Gemini 1.5 Discord Bot

A Discord bot powered by Google's Gemini 1.5 AI model that responds to user messages. This bot is designed to be hosted on pythonanywhere.com.

## Features

- Responds to text prompts using Gemini 1.5 AI
- Simple command structure with prefix customization
- Built-in cooldowns to prevent abuse
- Comprehensive error handling
- Detailed logging for debugging

## Requirements

- Python 3.9+
- discord.py
- google-generativeai
- python-dotenv

## Setup Instructions

### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Navigate to the "Bot" tab and click "Add Bot"
4. Under the "Privileged Gateway Intents" section, enable:
   - Message Content Intent
5. Copy your bot token (you'll need this later)
6. Use the OAuth2 URL Generator in the Discord Developer Portal to create an invite link with the following permissions:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands

### 2. Get a Gemini API Key

1. Go to the [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy your API key (you'll need this later)

### 3. Setup on PythonAnywhere

1. Sign up for a [PythonAnywhere account](https://www.pythonanywhere.com/) if you don't have one
2. Create a new console (Bash)
3. Clone this repository:
   ```
   git clone <repository-url>
   cd gemini-discord-bot
   