#!/usr/bin/env python3
"""
Main entry point for the Discord bot powered by Gemini 1.5 AI.
This file initializes and runs the bot.

It also provides the Flask application for web hosting when imported by gunicorn.
"""
import os
import logging
import threading
import sys
import discord
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
from utils.logger import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

# Check if we're running in the Discord bot workflow
is_discord_workflow = os.environ.get("REPL_WORKFLOW_NAME") == "run_discord_bot"

# If we're in the Discord workflow, mock out Flask to prevent port conflicts
if is_discord_workflow:
    logger.info("Detected run_discord_bot workflow - running bot only mode")
    # Create mock Flask module to prevent port conflicts
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
        
    # Mock out flask before it gets imported anywhere
    sys.modules['flask'] = MockModule()
    sys.modules['flask_sqlalchemy'] = type('MockSQLAlchemy', (), {
        '__getattr__': lambda self, name: lambda *args, **kwargs: None
    })()
    
    # Import bot directly
    from bot import GeminiBot
else:
    # Only import Flask if we're not in the Discord workflow
    from app import app
    from bot import GeminiBot

def start_bot():
    """Start the Discord bot in a separate thread"""
    logger.info("Starting Gemini Discord Bot...")
    
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
    if is_discord_workflow:
        # Start only the bot when in workflow mode
        start_bot()
    else:
        # When run normally, we'll start both the Flask app and the Discord bot
        # Start the bot in a separate thread
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True  # This makes the thread exit when the main program exits
        bot_thread.start()
        
        # Start the Flask app
        app.run(host="0.0.0.0", port=5000, debug=True)
