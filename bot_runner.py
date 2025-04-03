#!/usr/bin/env python3
"""
Bot runner script to start only the Discord bot without the web interface.
This is used by the run_discord_bot workflow.
"""
import os
import logging
from dotenv import load_dotenv
from bot import GeminiBot

# Load environment variables
load_dotenv()

# Configure logging
from utils.logger import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Gemini Discord Bot...")
    
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