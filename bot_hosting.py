
import os
import logging
from dotenv import load_dotenv
from bot import GeminiBot

# Configure logging for external hosting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discord_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def start_bot():
    """Start the Discord bot for external hosting"""
    logger.info("Starting Discord bot...")
    
    # Load environment variables
    load_dotenv()
    
    # Get Discord token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables")
        return
        
    try:
        # Initialize and run bot
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    start_bot()
