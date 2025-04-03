"""
Configuration module for the Discord bot.
Contains various settings and constants used throughout the application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_PREFIX = os.getenv("BOT_PREFIX", "!") 
BOT_DESCRIPTION = "A Discord bot powered by Gemini 1.5 AI"
BOT_STATUS = "Powered by Gemini 1.5"

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "1024"))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
GEMINI_TOP_P = float(os.getenv("GEMINI_TOP_P", "0.9"))
GEMINI_TOP_K = int(os.getenv("GEMINI_TOP_K", "40"))

# Message configuration
MAX_RESPONSE_LENGTH = 1900  # Discord message character limit is 2000, leaving some buffer
RESPONSE_FOOTER = "\n\n*Powered by Gemini 1.5 AI*"

# Cooldown settings (in seconds)
COMMAND_COOLDOWN = int(os.getenv("COMMAND_COOLDOWN", "5"))
