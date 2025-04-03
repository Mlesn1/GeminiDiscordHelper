#!/usr/bin/env python3
"""
Special entry point for running the Discord bot in the Replit workflow.
This file completely avoids importing Flask, preventing port conflicts.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from bot import GeminiBot
from utils.logger import setup_logger

# Block Flask imports before importing anything else
sys.modules['flask'] = type('MockFlask', (), {
    '__getattr__': lambda self, name: lambda *args, **kwargs: None
})()

# Load environment variables from .env file
load_dotenv()

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

def start_bot():
    """
    Initializes and starts the Discord bot without any web components
    """
    logger.info("Starting Discord bot from workflow...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        exit(1)
    
    try:    
        # Initialize and run the bot
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        exit(1)

if __name__ == "__main__":
    start_bot()