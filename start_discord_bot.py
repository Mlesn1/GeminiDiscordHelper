#!/usr/bin/env python3
"""
Simplified starter script for running only the Discord bot.
This script completely avoids importing Flask to prevent port conflicts.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from utils.logger import setup_logger

# Block all Flask imports before any other imports
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
    
# Mock Flask and related imports
sys.modules['flask'] = MockModule()
sys.modules['flask_sqlalchemy'] = type('MockSQLAlchemy', (), {
    '__getattr__': lambda self, name: lambda *args, **kwargs: None
})

# Load environment variables
load_dotenv()

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

def start_bot():
    """
    Initialize and start the Discord bot without Flask
    """
    logger.info("Starting Discord bot standalone (via start_discord_bot.py)...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        sys.exit(1)
    
    # Import bot here after Flask has been mocked
    from bot import GeminiBot
    
    try:    
        # Initialize and run the bot
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # This is a direct standalone run - don't try to import app.py
    start_bot()