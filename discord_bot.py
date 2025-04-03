#!/usr/bin/env python3
"""
Simple standalone Discord bot entry point.
This file is explicitly designed to avoid any Flask imports or port bindings.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from bot import GeminiBot
from utils.logger import setup_logger

# Block Flask from being imported by anything
sys.modules['flask'] = type('MockFlask', (), {
    'Flask': type('MockFlaskClass', (), {
        '__init__': lambda *args, **kwargs: None,
        '__getattr__': lambda self, name: lambda *args, **kwargs: None
    })
})

# Load environment variables
load_dotenv()

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

def start_bot():
    """Start the Discord bot only - no web components"""
    logger.info("Starting Discord bot standalone...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        sys.exit(1)
    
    try:    
        # Initialize and run the bot
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the bot
    start_bot()

# If imported as a module, automatically start the bot
start_bot()