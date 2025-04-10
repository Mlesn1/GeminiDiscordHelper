#!/usr/bin/env python3
"""
Dedicated entry point for running ONLY the Discord bot without the Flask web interface.
This file is specifically designed for the run_discord_bot workflow.
"""
import os
import sys
import logging
import threading
import importlib.util
from types import ModuleType

# Mock Flask to prevent it from being imported by other modules
class MockFlask:
    def __init__(self, *args, **kwargs):
        pass
        
    def route(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator
        
    def run(self, *args, **kwargs):
        pass
        
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class MockModule:
    Flask = MockFlask
    
# Install the mock
sys.modules['flask'] = MockModule()

# Configure logging
from utils.logger import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from bot import GeminiBot
import discord

def start_bot():
    """
    Initialize and start the Discord bot (no Flask)
    """
    logger.info("Starting Discord bot in standalone mode...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        return
    
    try:
        # Initialize and run the bot
        bot = GeminiBot()
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
    start_bot()