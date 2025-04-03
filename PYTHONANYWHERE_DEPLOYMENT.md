# PythonAnywhere Deployment Guide

This guide explains how to deploy the Gemini Discord Bot on PythonAnywhere.com. PythonAnywhere is a cloud-based Python development and hosting environment that makes it easy to host your Discord bot.

## Prerequisites

- A PythonAnywhere account (free tier is sufficient)
- A Discord bot token
- A Google Gemini API key

## Deployment Options

You have two main options for deploying the bot:

1. **Web App + Bot**: Run both the Flask web interface and the Discord bot
2. **Bot Only**: Run only the Discord bot as an "Always-on task"

## Option 1: Web App + Bot (Recommended)

This option runs both the web interface and the Discord bot, giving you a nice dashboard to monitor the bot's status.

### Step 1: Upload Files to PythonAnywhere

1. Log in to your PythonAnywhere account
2. Open a Bash console
3. Clone this repository:
   ```bash
   git clone <repository-url>
   cd gemini-discord-bot
   ```

### Step 2: Install Dependencies

```bash
pip install --user discord.py google-generativeai python-dotenv flask gunicorn
```

### Step 3: Set Up Environment Variables

Create a `.env` file with your API keys:

```bash
echo "DISCORD_TOKEN=your_discord_bot_token" > .env
echo "GEMINI_API_KEY=your_gemini_api_key" >> .env
```

### Step 4: Configure Web App

1. Go to the Web tab in PythonAnywhere
2. Click "Add a new web app"
3. Choose the "Manual configuration" option
4. Select Python 3.9 (or later)
5. Set the source code directory to your project folder
6. Edit the WSGI configuration file:

```python
import os
import sys

# Add your project directory to the Python path
project_path = '/home/<your-username>/gemini-discord-bot'
if project_path not in sys.path:
    sys.path.append(project_path)

# Set environment variables for your API keys
os.environ["DISCORD_TOKEN"] = "your_discord_bot_token"
os.environ["GEMINI_API_KEY"] = "your_gemini_api_key"

# Import the Flask app
from app import app as application
```

7. Save the WSGI file
8. Reload your web app

## Option 2: Bot Only (Always-on Task)

This option runs only the Discord bot without the web interface, using an "Always-on task" (paid accounts only).

### Step 1: Upload Files to PythonAnywhere

1. Log in to your PythonAnywhere account
2. Open a Bash console
3. Clone this repository:
   ```bash
   git clone <repository-url>
   cd gemini-discord-bot
   ```

### Step 2: Install Dependencies

```bash
pip install --user discord.py google-generativeai python-dotenv
```

### Step 3: Set Up Environment Variables

Create a `.env` file with your API keys:

```bash
echo "DISCORD_TOKEN=your_discord_bot_token" > .env
echo "GEMINI_API_KEY=your_gemini_api_key" >> .env
```

### Step 4: Create an Always-on Task

1. Go to the Tasks tab in PythonAnywhere
2. Add a new Always-on task with this command:
   ```bash
   cd /home/<your-username>/gemini-discord-bot && python standalone_bot.py
   ```

## Checking Logs and Troubleshooting

### Logs Location

- Web app logs: Found in the Logs section of the Web tab
- Task logs: Found in the Tasks tab
- Bot logs: Located in the `logs` directory of your project

### Common Issues

1. **Port 5000 in use error**: Use `standalone_bot.py` which avoids Flask completely
2. **429 Too Many Requests**: Discord rate limit - wait before retrying
3. **Unauthorized error**: Check your Discord token
4. **403 Forbidden error**: Check your bot's permissions

### Required Environment Variables

- `DISCORD_TOKEN`: Your Discord bot token
- `GEMINI_API_KEY`: Your Google Gemini API key

## Running Bot Locally During Development

For local testing, you can run:

```bash
# To run both web interface and bot:
python main.py

# To run only the bot without any web interface:
python standalone_bot.py
```

## Free vs Paid PythonAnywhere

- **Free tier**: Can only use the web app option, which will run for 3 months without interaction
- **Paid tier**: Can use either option, with Always-on tasks available for continuous operation

## Resource Usage

The bot is very lightweight:
- Code size: ~100KB
- Memory usage: ~50-100MB
- CPU: Minimal
- Storage: Well under the 512MB free tier limit