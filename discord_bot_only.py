#!/usr/bin/env python3
"""
Dedicated entry point for running ONLY the Discord bot without the Flask web interface.
This file is specifically designed for the run_discord_bot workflow.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from bot import GeminiBot
from utils.logger import setup_logger

# Before any Flask imports, monkey patch the flask module
# Mock Flask to prevent it from being imported and trying to start a server
class MockFlask:
    def __init__(self, *args, **kwargs):
        pass
    def route(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator
    def run(self, *args, **kwargs):
        # Do nothing when run is called
        pass
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class MockModule:
    Flask = MockFlask
    
# Install the mock to block any Flask imports
sys.modules['flask'] = MockModule()

# Disable calls to app.run in imported modules
if 'app' in sys.modules:
    app_module = sys.modules['app']
    if hasattr(app_module, 'app') and hasattr(app_module.app, 'run'):
        app_module.app.run = lambda *args, **kwargs: None

# Load environment variables
load_dotenv()

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

def start_bot():
    """
    Initialize and start the Discord bot (no Flask)
    """
    logger.info("Starting Gemini Discord Bot (no web interface)...")
    
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