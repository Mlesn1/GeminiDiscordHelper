#!/usr/bin/env python3
"""
Special entry point for running the Discord bot in the Replit workflow.
This file completely avoids importing Flask, preventing port conflicts.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

def start_bot():
    """
    Initializes and starts the Discord bot without any web components
    """
    logger.info("Starting Discord bot from workflow (run_discord_bot_workflow.py)...")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        sys.exit(1)
    
    # Block Flask imports before moving on
    sys.modules['flask'] = type('MockModule', (), {
        'Flask': type('MockFlask', (), {'__init__': lambda *args, **kwargs: None, 
                                        '__getattr__': lambda *args, **kwargs: lambda *a, **k: None})
    })
    sys.modules['flask_sqlalchemy'] = type('MockSQLAlchemy', (), {
        '__getattr__': lambda self, name: lambda *args, **kwargs: None
    })
    
    # Import bot after blocking Flask
    from bot import GeminiBot
    
    try:    
        # Initialize and run the bot
        bot = GeminiBot()
        logger.info("Bot initialized, connecting to Discord...")
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the bot
    start_bot()