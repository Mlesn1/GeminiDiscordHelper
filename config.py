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
AUTO_RESPONSE_CHANNELS = [1234567890]  # Replace with your channel ID
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

# Personality and Mood Settings
ENABLE_MOOD_INDICATOR = os.getenv("ENABLE_MOOD_INDICATOR", "true").lower() == "true"
MOOD_CHANGE_PROBABILITY = float(os.getenv("MOOD_CHANGE_PROBABILITY", "0.2"))  # Probability to change mood (0.0-1.0)
ENABLE_ENERGY_METER = os.getenv("ENABLE_ENERGY_METER", "true").lower() == "true"
DEFAULT_PERSONALITY = os.getenv("DEFAULT_PERSONALITY", "balanced")
USER_SELECTABLE_PERSONALITY = os.getenv("USER_SELECTABLE_PERSONALITY", "true").lower() == "true"

# Personality definitions
PERSONALITIES = {
    "balanced": {
        "name": "Balanced",
        "description": "A well-rounded assistant that balances helpfulness, creativity, and precision.",
        "gemini_params": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40
        },
        "style_guide": "Balanced and adaptable, I provide comprehensive but concise answers.",
        "emoji": "⚖️"
    },
    "creative": {
        "name": "Creative",
        "description": "Emphasizes creative and imaginative responses with more varied output.",
        "gemini_params": {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 50
        },
        "style_guide": "I'm particularly creative and expressive, offering imaginative and detailed responses.",
        "emoji": "🎨"
    },
    "precise": {
        "name": "Precise",
        "description": "Focuses on accuracy and conciseness with less creative variation.",
        "gemini_params": {
            "temperature": 0.3,
            "top_p": 0.75,
            "top_k": 20
        },
        "style_guide": "I'm precise and to-the-point, focusing on accuracy and brevity.",
        "emoji": "🎯"
    },
    "friendly": {
        "name": "Friendly",
        "description": "Warm and conversational, with a focus on approachability.",
        "gemini_params": {
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 45
        },
        "style_guide": "I'm warm, friendly, and conversational, like talking to a helpful friend.",
        "emoji": "🤗"
    },
    "technical": {
        "name": "Technical",
        "description": "Specializes in detailed technical explanations with appropriate terminology.",
        "gemini_params": {
            "temperature": 0.5,
            "top_p": 0.85,
            "top_k": 30
        },
        "style_guide": "I focus on technical accuracy and detail, using appropriate terminology and structure.",
        "emoji": "🔧"
    }
}

# Mood definitions and their emoji indicators
MOODS = {
    "happy": {
        "emoji": "😊",
        "prefixes": ["Happily, ", "With joy, ", "Excitedly, "],
        "suffixes": [" Feeling cheerful today!", " That was fun to answer!", " Hope that helps!"],
        "energy": 5  # High energy
    },
    "thoughtful": {
        "emoji": "🤔",
        "prefixes": ["Hmm, ", "Let me think... ", "Considering that, "],
        "suffixes": [" Still pondering this one...", " Quite an interesting question!", " What do you think?"],
        "energy": 3  # Medium energy
    },
    "curious": {
        "emoji": "🧐",
        "prefixes": ["Interestingly, ", "Curiously, ", "I wonder... "],
        "suffixes": [" That's fascinating!", " I'd like to learn more about that.", " What else can we explore here?"],
        "energy": 4  # Medium-high energy
    },
    "playful": {
        "emoji": "😏",
        "prefixes": ["Oh! ", "Fun fact: ", "Ready for this? "],
        "suffixes": [" Bet you didn't expect that answer!", " That's a fun one!", " *winks*"],
        "energy": 5  # High energy
    },
    "professional": {
        "emoji": "👨‍💼",
        "prefixes": ["Professionally speaking, ", "According to best practices, ", "In my analysis, "],
        "suffixes": [" Hope that clarifies things.", " Let me know if you need more specific information.", " Is there anything else you'd like to know?"],
        "energy": 2  # Lower energy
    },
    "calm": {
        "emoji": "😌",
        "prefixes": ["Calmly, ", "With measured thought, ", "Serenely, "],
        "suffixes": [" Take your time to digest that.", " How does that resonate with you?", " I'm here whenever you're ready for more."],
        "energy": 1  # Very low energy
    },
    "excited": {
        "emoji": "🤩",
        "prefixes": ["WOW! ", "How exciting! ", "Oh my goodness! "],
        "suffixes": [" Isn't that AMAZING?!", " This is so cool!", " I'm thrilled to share this with you!"],
        "energy": 5  # Maximum energy
    }
}

# Energy level emojis (0 lowest, 5 highest)
ENERGY_LEVEL_INDICATORS = {
    0: "🔋",  # Empty battery
    1: "⚡",   # Low energy
    2: "⚡⚡",  # Medium-low energy
    3: "⚡⚡⚡", # Medium energy
    4: "⚡⚡⚡⚡", # Medium-high energy
    5: "⚡⚡⚡⚡⚡" # Full energy
}

# Default mood
DEFAULT_MOOD = "thoughtful"