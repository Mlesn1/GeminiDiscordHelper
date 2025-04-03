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
- flask (for web interface)
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
   ```
4. Install the required packages:
   ```
   pip install --user discord.py google-generativeai python-dotenv flask gunicorn
   ```
5. Create a `.env` file with your API keys:
   ```
   echo "DISCORD_TOKEN=your_discord_bot_token" > .env
   echo "GEMINI_API_KEY=your_gemini_api_key" >> .env
   ```

### 4. Deployment Options (Choose One)

#### Option 1: Web App + Bot (Recommended)

This option provides both the Discord bot functionality and a web interface for status monitoring.

1. Set up a web app in PythonAnywhere:
   - Go to the "Web" tab and create a new web app
   - Choose "Manual configuration" (not WSGI)
   - Select Python 3.9 or higher

2. Configure the web app:
   - Set the source directory to your project folder
   - Set the WSGI configuration file to point to your project
   - Edit the WSGI configuration file:
   
   ```python
   import sys
   import os
   
   # Add your project directory to the Python path
   project_path = '/home/yourusername/gemini-discord-bot'
   if project_path not in sys.path:
       sys.path.append(project_path)
   
   # Set environment variables for your API keys
   os.environ["DISCORD_TOKEN"] = "your_discord_bot_token"
   os.environ["GEMINI_API_KEY"] = "your_gemini_api_key"
   
   # Import the Flask app from your project
   from app import app as application
   ```

3. Restart your web app from the PythonAnywhere dashboard

#### Option 2: Bot Only (Always-on Task)

If you only want to run the bot without the web interface:

1. Go to the "Consoles" tab in PythonAnywhere
2. Start a new "Always-on task" with the command:
   ```
   cd ~/gemini-discord-bot && python pythonanywhere_bot.py
   ```
3. This will run the bot continuously without the web interface

### 5. Troubleshooting

- If you see "Port 5000 is in use" errors, use the discord_bot_only.py script to run only the Discord bot
- Check the logs folder for detailed error information
- Ensure your DISCORD_TOKEN and GEMINI_API_KEY are correctly set in your environment

## Commands

- `!ask <your question>` - Ask the AI a question
- `!about` - Display information about the bot

## Resource Usage

The bot is very lightweight and well-suited for PythonAnywhere's free tier:
- Code files: ~100KB
- Memory usage: ~50-100MB
- CPU: Minimal usage
- Storage: Well under the 512MB free tier limit

## License

MIT