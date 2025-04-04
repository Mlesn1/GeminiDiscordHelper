"""
PythonAnywhere deployment script for Gemini Discord Bot
This script runs the Discord bot without any web interface
to avoid port conflicts on PythonAnywhere.
"""

import os
import time
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pythonanywhere_discord.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for PythonAnywhere deployment."""
    # Load environment variables from .env file if it exists
    if os.path.exists(".env"):
        load_dotenv()
        logger.info("Loaded environment variables from .env file")
    
    # Check for Discord token
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        print("ERROR: DISCORD_TOKEN not found. Make sure to set it in your .env file or PythonAnywhere environment.")
        return
    
    # Check for Gemini API key
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.critical("GEMINI_API_KEY not found in environment variables. Bot cannot start.")
        print("ERROR: GEMINI_API_KEY not found. Make sure to set it in your .env file or PythonAnywhere environment.")
        return
    
    logger.info("Starting Discord bot on PythonAnywhere...")
    print("Starting Discord bot on PythonAnywhere...")
    
    # Import and run the clean bot
    try:
        from clean_bot import main as start_bot
        start_bot()
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        print(f"ERROR: Failed to start bot: {e}")
        
        # Wait a bit before restarting
        time.sleep(10)
        logger.info("Attempting to restart...")
        main()  # Try again

if __name__ == "__main__":
    print("=" * 50)
    print("GEMINI DISCORD BOT - PYTHONANYWHERE DEPLOYMENT")
    print("=" * 50)
    main()