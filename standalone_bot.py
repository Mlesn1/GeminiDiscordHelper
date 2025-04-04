#!/usr/bin/env python3
"""
Standalone entry point for the Discord bot without any web components.
This script avoids importing Flask entirely, solving port conflicts.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from bot import GeminiBot
from utils.logger import setup_logger

# Block any Flask imports to prevent port conflicts
sys.modules['flask'] = type('DisabledFlask', (), {
    '__getattr__': lambda self, name: lambda *args, **kwargs: None
})()

# Load environment variables
load_dotenv()

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

def start_bot():
    """
    Initialize and start only the Discord bot (no web interface)
    """
    logger.info("Starting Gemini Discord Bot standalone (no web interface)...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        exit(1)
    
    try:    
        # Initialize and run the bot
        bot = GeminiBot()
        # Add retry strategy for handling rate limits
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        # If we have a rate limit error, wait before exiting
        if "429 Too Many Requests" in str(e):
            logger.warning("Discord rate limit exceeded. Try again later.")
            # Exit with a temporary failure code to allow for restart
            exit(75)  # EX_TEMPFAIL from sysexits.h
        exit(1)
        
if __name__ == "__main__":
    start_bot()