#!/usr/bin/env python3
"""
Entry point for running the Discord bot on PythonAnywhere.
This file is specifically designed to work in PythonAnywhere's environment.

To use this file:
1. Upload it to your PythonAnywhere account
2. Set up an "Always-on task" that runs: python pythonanywhere_bot.py
3. This will keep your bot running continuously
"""
import os
import sys
import logging
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discord_bot.log")
    ]
)
logger = logging.getLogger(__name__)

def start_bot():
    """
    Initialize and start the Discord bot
    """
    logger.info("Starting Discord bot on PythonAnywhere...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        sys.exit(1)
    
    # Import the bot class
    from bot import GeminiBot
    
    try:    
        # Initialize and run the bot
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Set environment variable to identify we're on PythonAnywhere
    os.environ["PYTHONANYWHERE_DOMAIN"] = "true"
    
    # Start the bot
    start_bot()