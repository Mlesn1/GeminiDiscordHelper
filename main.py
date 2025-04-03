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
import subprocess

# Configure logging first
from utils.logger import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

# Print all environment variables for debugging
print("=" * 50)
print("ENVIRONMENT VARIABLES:")
for key, value in os.environ.items():
    print(f"  {key}: {value}")
print("=" * 50)

# Special handling for running in the Discord bot workflow
# Check various indicators to detect the Discord bot workflow
workflow_signals = [
    os.environ.get("REPL_WORKFLOW_NAME", "").lower() == "run_discord_bot",
    os.environ.get("DISCORD_BOT_WORKFLOW") == "1",
    "discord_bot" in sys.argv[0].lower() if sys.argv else False,
    any("discord" in arg.lower() for arg in sys.argv) if sys.argv else False
]

if any(workflow_signals):
    print("=" * 50)
    print("DETECTED DISCORD BOT WORKFLOW - STARTING CLEAN BOT")
    print("=" * 50)
    logger.info("Detected Discord bot workflow environment, running clean bot script")
    try:
        # Run the clean standalone bot
        with open("bot.pid", "w") as f:
            f.write(str(os.getpid()))
        exec(open("clean_bot.py").read())
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Failed to run clean_bot.py: {e}")
        print(f"Error running clean_bot.py: {e}")

# Check command line arguments for bot-only mode
bot_only_mode = "--bot-only" in sys.argv

# Also check environment variables and workflow configuration
# Directly check if this script is being run by the run_discord_bot workflow
import inspect
import os.path
caller_filename = os.path.basename(inspect.stack()[-1].filename)
is_discord_workflow = "run_discord_bot" in caller_filename or "discord_bot" in caller_filename

# Double check the workflow name if available
if os.environ.get("REPL_WORKFLOW_NAME"):
    is_discord_workflow = is_discord_workflow or "discord" in os.environ.get("REPL_WORKFLOW_NAME", "").lower()

# We're in bot-only mode if either condition is true
bot_only_mode = bot_only_mode or is_discord_workflow

# Get the workflow name for debugging
workflow_name = os.environ.get("REPL_WORKFLOW_NAME", "")

# Print debug information to help troubleshoot
print(f"Bot-only mode: {bot_only_mode}, CLI args: {sys.argv}")
print(f"Is discord workflow: {is_discord_workflow}")
print(f"Caller filename: {caller_filename}")
print(f"Workflow name: {workflow_name}")

if bot_only_mode:
    logger.info("Running in bot-only mode - no web interface")
    # Import only what we need for the bot
    from dotenv import load_dotenv
    import discord
    from bot import GeminiBot
    
    # Load environment variables
    load_dotenv()
    
    # We'll define app as None so later code doesn't fail
    app = None
else:
    # Normal mode with both Discord bot and web interface
    logger.info("Running in full mode with web interface")
    from dotenv import load_dotenv
    import discord
    
    # Load environment variables
    load_dotenv()
    
    # Import Flask and bot
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
    if bot_only_mode:
        # Start only the bot when in bot-only mode
        logger.info("Starting Discord bot in standalone mode")
        start_bot()
    else:
        # When run normally, we'll start both the Flask app and the Discord bot
        logger.info("Starting both Discord bot and web interface")
        
        # Start the bot in a separate thread
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True  # This makes the thread exit when the main program exits
        bot_thread.start()
        
        # Start the Flask app
        if app:  # Check that app exists
            app.run(host="0.0.0.0", port=5000, debug=True)
        else:
            logger.error("Flask app not initialized but trying to run in web mode")
