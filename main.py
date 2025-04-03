#!/usr/bin/env python3
"""
Main entry point for the Discord bot powered by Gemini 1.5 AI.
This file initializes and runs the bot.

It also provides the Flask application for web hosting when imported by gunicorn.
"""
import os
import logging
import threading
import discord
from dotenv import load_dotenv
from bot import GeminiBot

# Load environment variables
load_dotenv()

# Configure logging
from utils.logger import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

# Import Flask app for web interface
from app import app

# For gunicorn to work, we need to provide the app variable
# This is the Flask application that will be served

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
    # Check if this is running under the run_discord_bot workflow
    if os.environ.get("REPL_WORKFLOW_NAME") == "run_discord_bot":
        # Just start the bot directly, no Flask
        import sys
        sys.argv = [sys.argv[0]]  # Clear command line args to prevent Flask from parsing them
        from discord_bot_only import start_bot as start_bot_only
        start_bot_only()
    else:
        # When run normally, we'll start both the Flask app and the Discord bot
        # Start the bot in a separate thread
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True  # This makes the thread exit when the main program exits
        bot_thread.start()
        
        # Start the Flask app
        app.run(host="0.0.0.0", port=5000, debug=True)
