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
BOT_STATUS = os.getenv("BOT_STATUS", "Powered by Gemini 1.5")

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "1024"))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
GEMINI_TOP_P = float(os.getenv("GEMINI_TOP_P", "0.9"))
GEMINI_TOP_K = int(os.getenv("GEMINI_TOP_K", "40"))
GEMINI_SYSTEM_INSTRUCTIONS = os.getenv("GEMINI_SYSTEM_INSTRUCTIONS", 
    "You are a helpful, creative, and friendly AI assistant named Gemini. You are having a conversation through Discord.")

# Auto-response configuration
# Comma-separated list of channel IDs where the bot should respond to all messages
AUTO_RESPONSE_CHANNELS = [int(id.strip()) for id in os.getenv("AUTO_RESPONSE_CHANNELS", "").split(",") if id.strip().isdigit()]
AUTO_RESPONSE_IGNORE_PREFIX = os.getenv("AUTO_RESPONSE_IGNORE_PREFIX", "!").split(",")
AUTO_RESPONSE_COOLDOWN = int(os.getenv("AUTO_RESPONSE_COOLDOWN", "10"))

# Message configuration
MAX_RESPONSE_LENGTH = 1900  # Discord message character limit is 2000, leaving some buffer
RESPONSE_FOOTER = "\n\n*Powered by Gemini 1.5 AI*"

# Cooldown settings (in seconds)
COMMAND_COOLDOWN = int(os.getenv("COMMAND_COOLDOWN", "5"))

# Conversation memory settings
ENABLE_CONVERSATION_MEMORY = os.getenv("ENABLE_CONVERSATION_MEMORY", "true").lower() == "true"
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))  # Number of messages to remember
CONVERSATION_MEMORY_EXPIRY = int(os.getenv("CONVERSATION_MEMORY_EXPIRY", "3600"))  # Seconds until memory expires (1 hour)
CONVERSATION_PREVIEW_LENGTH = int(os.getenv("CONVERSATION_PREVIEW_LENGTH", "3"))  # Number of past messages to show in preview

# Admin settings
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Bot Admin")  # Role name for bot administrators
BOT_OWNERS = [int(id.strip()) for id in os.getenv("BOT_OWNERS", "").split(",") if id.strip().isdigit()]  # List of user IDs with owner privileges

# Mood indicator settings
ENABLE_MOOD_INDICATOR = os.getenv("ENABLE_MOOD_INDICATOR", "true").lower() == "true"
MOOD_CHANGE_PROBABILITY = float(os.getenv("MOOD_CHANGE_PROBABILITY", "0.2"))  # Probability to change mood (0.0-1.0)

# Mood definitions and their emoji indicators
MOODS = {
    "happy": {
        "emoji": "😊",
        "prefixes": ["Happily, ", "With joy, ", "Excitedly, "],
        "suffixes": [" Feeling cheerful today!", " That was fun to answer!", " Hope that helps!"]
    },
    "thoughtful": {
        "emoji": "🤔",
        "prefixes": ["Hmm, ", "Let me think... ", "Considering that, "],
        "suffixes": [" Still pondering this one...", " Quite an interesting question!", " What do you think?"]
    },
    "curious": {
        "emoji": "🧐",
        "prefixes": ["Interestingly, ", "Curiously, ", "I wonder... "],
        "suffixes": [" That's fascinating!", " I'd like to learn more about that.", " What else can we explore here?"]
    },
    "playful": {
        "emoji": "😏",
        "prefixes": ["Oh! ", "Fun fact: ", "Ready for this? "],
        "suffixes": [" Bet you didn't expect that answer!", " That's a fun one!", " *winks*"]
    },
    "professional": {
        "emoji": "👨‍💼",
        "prefixes": ["Professionally speaking, ", "According to best practices, ", "In my analysis, "],
        "suffixes": [" Hope that clarifies things.", " Let me know if you need more specific information.", " Is there anything else you'd like to know?"]
    }
}

# Default mood
DEFAULT_MOOD = "thoughtful"
