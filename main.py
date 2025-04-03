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

# ========================================================
# DISCORD BOT WORKFLOW DETECTION - IMMEDIATE REDIRECTION
# This runs before anything else to prevent port conflicts
# ========================================================

# We put this at the very top, before any imports that might 
# cause conflicts, to correctly identify and redirect to the standalone script
argv_str = " ".join(sys.argv).lower() if sys.argv else ""
script_name = sys.argv[0].lower() if sys.argv else ""
env_workflow = os.environ.get("REPL_WORKFLOW_NAME", "").lower()

# Use explicit environment flag for most reliable detection
discord_bot_env = os.environ.get("DISCORD_BOT_WORKFLOW_ONLY", "0") == "1"

# VERY specific detection for the run_discord_bot workflow
# This should ONLY match when we're truly in the discord bot workflow
if (discord_bot_env or                                           # Explicit flag
    (env_workflow == "run_discord_bot") or                        # Exact workflow name match
    ("run_discord_bot.sh" in argv_str) or                         # Script name match
    ("discord_bot_standalone.py" in argv_str) or                  # Explicit standalone script
    ("clean_bot.py" in argv_str) or                               # Our new clean bot script
    (os.path.exists("bot.pid") and not                           # PID file exists AND
     (sys.argv and "gunicorn" in " ".join(sys.argv).lower()))):  # NOT gunicorn

    # Avoid importing the app if we're in the discord bot workflow
    print("=" * 80)
    print("VERY EARLY DETECTION: DISCORD BOT WORKFLOW DETECTED!")
    print("REDIRECTING TO STANDALONE BOT - AVOIDING PORT CONFLICTS")
    print("=" * 80)
    
    # Create a process ID file to mark this as a bot process
    with open("bot.pid", "w") as f:
        f.write(str(os.getpid()))
    
    # Use os.execv for a clean replacement of the current process
    os.execv(sys.executable, [sys.executable, "clean_bot.py"])
    
    # Failsafe in case execv doesn't work
    sys.exit(0)

# Configure logging first
from utils.logger import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

# Print workflow information for debugging
print("=" * 50)
print(f"WORKFLOW: {os.environ.get('REPL_WORKFLOW_NAME', 'unknown')}")
print(f"ARGV: {sys.argv}")
print("=" * 50)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask and bot
from app import app

# Import what we need for the bot
import discord
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
    # When run directly, we'll start both the Flask app and the Discord bot
    logger.info("Starting both Discord bot and web interface")
    
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True  # This makes the thread exit when the main program exits
    bot_thread.start()
    
    # Start the Flask app - gunicorn will be used in the workflow
    if app:  # Check that app exists
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        logger.error("Flask app not initialized but trying to run in web mode")
