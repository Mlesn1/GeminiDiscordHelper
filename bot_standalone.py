#!/usr/bin/env python3
"""
Standalone Discord bot without any Flask components.
This script is specifically designed for running only the Discord bot without any web interface.
"""
import os
import sys
import logging
import discord
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
from utils.logger import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

from bot import GeminiBot

def start_bot():
    """Start the Discord bot without Flask"""
    logger.info("Starting Discord bot standalone mode...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        return
    
    try:    
        # Initialize and run the bot
        bot = GeminiBot()
        # Add retry strategy for handling rate limits
        bot.run(token, reconnect=True)
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit error
            logger.warning(f"Discord rate limit exceeded. Try again later: {e}")
            # Sleep for a bit to allow rate limits to reset
            import time
            time.sleep(60)  # Wait 60 seconds before trying again
        else:
            logger.error(f"Discord HTTP error: {e}")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    # This script only runs the Discord bot
    start_bot()