#!/usr/bin/env python3
"""
Completely standalone Discord bot with no Flask components or port conflicts.
This is the primary script that should be used in the 'run_discord_bot' workflow.
"""
import os
import sys
import logging
import random
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Ensure we have a logs directory
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/discord_bot.log')
    ]
)
logger = logging.getLogger(__name__)

print("=" * 50)
print("STARTING CLEAN DISCORD BOT WITH NO FLASK COMPONENTS")
print("=" * 50)
logger.info("Starting clean Discord bot with no Flask components")

# Load environment variables from .env if possible
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
    
    # Set database URL if needed
    if "DATABASE_URL" not in os.environ and all(key in os.environ for key in ["PGUSER", "PGPASSWORD", "PGHOST", "PGPORT", "PGDATABASE"]):
        # Construct DATABASE_URL from individual components
        pg_user = os.environ["PGUSER"]
        pg_password = os.environ["PGPASSWORD"]
        pg_host = os.environ["PGHOST"]
        pg_port = os.environ["PGPORT"]
        pg_database = os.environ["PGDATABASE"]
        os.environ["DATABASE_URL"] = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        logger.info("Constructed DATABASE_URL from individual PostgreSQL environment variables")
except ImportError:
    logger.warning("dotenv package not found, skipping .env file loading")

# Import Discord-related modules
import discord
from discord.ext import commands
import google.generativeai as genai

# Configuration variables
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
AUTO_RESPONSE_CHANNELS = [int(id.strip()) for id in os.getenv("AUTO_RESPONSE_CHANNELS", "").split(",") if id.strip().isdigit()]
AUTO_RESPONSE_IGNORE_PREFIX = os.getenv("AUTO_RESPONSE_IGNORE_PREFIX", "!").split(",")
AUTO_RESPONSE_COOLDOWN = int(os.getenv("AUTO_RESPONSE_COOLDOWN", "10"))
ENABLE_MENTION_RESPONSES = os.getenv("ENABLE_MENTION_RESPONSES", "true").lower() == "true"
ENABLE_DIRECT_MESSAGE_RESPONSES = os.getenv("ENABLE_DIRECT_MESSAGE_RESPONSES", "true").lower() == "true"

# Message configuration
MAX_RESPONSE_LENGTH = 1900  # Discord message character limit is 2000, leaving some buffer
RESPONSE_FOOTER = "\n\n*Powered by Gemini 1.5 AI*"

# Cooldown settings (in seconds)
COMMAND_COOLDOWN = int(os.getenv("COMMAND_COOLDOWN", "5"))

# Conversation memory settings
ENABLE_CONVERSATION_MEMORY = os.getenv("ENABLE_CONVERSATION_MEMORY", "true").lower() == "true"
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
CONVERSATION_MEMORY_EXPIRY = int(os.getenv("CONVERSATION_MEMORY_EXPIRY", "3600"))
CONVERSATION_PREVIEW_LENGTH = int(os.getenv("CONVERSATION_PREVIEW_LENGTH", "3"))

# Admin settings
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Bot Admin")
BOT_OWNERS = [int(id.strip()) for id in os.getenv("BOT_OWNERS", "").split(",") if id.strip().isdigit()]

# Mood indicator settings
ENABLE_MOOD_INDICATOR = os.getenv("ENABLE_MOOD_INDICATOR", "true").lower() == "true"
MOOD_CHANGE_PROBABILITY = float(os.getenv("MOOD_CHANGE_PROBABILITY", "0.2"))
ENABLE_ENERGY_METER = os.getenv("ENABLE_ENERGY_METER", "true").lower() == "true"
DEFAULT_PERSONALITY = os.getenv("DEFAULT_PERSONALITY", "balanced")
USER_SELECTABLE_PERSONALITY = os.getenv("USER_SELECTABLE_PERSONALITY", "true").lower() == "true"

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

# Cooldown tracking for rate limiting
channel_cooldowns: Dict[int, float] = {}  # Channel-based cooldowns
user_cooldowns: Dict[int, float] = {}     # User-based cooldowns
user_channel_cooldowns: Dict[str, float] = {}  # Combined user+channel cooldowns

@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float = field(default_factory=time.time)
    author_name: str = ""  # Name of the person who sent the message
    author_id: int = 0  # Discord ID of the person


@dataclass
class Conversation:
    """Represents a conversation with history."""
    messages: List[Message] = field(default_factory=list)
    last_activity: float = field(default_factory=time.time)
    mood: str = DEFAULT_MOOD
    personality: str = DEFAULT_PERSONALITY
    energy_level: int = 3  # Default medium energy
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history."""
        self.messages.append(message)
        self.last_activity = time.time()
        
        # Keep only the most recent messages up to MAX_CONVERSATION_HISTORY
        if len(self.messages) > MAX_CONVERSATION_HISTORY:
            self.messages = self.messages[-MAX_CONVERSATION_HISTORY:]
            
        # Update energy level based on message content and current mood
        if ENABLE_ENERGY_METER:
            self._update_energy_level(message)
            
    def _update_energy_level(self, message: Message) -> None:
        """
        Update the conversation energy level based on the new message.
        
        The energy level is influenced by:
        - Current mood's natural energy level
        - Message length (longer messages increase energy)
        - Message content (exclamation marks, question marks, capitals)
        - Message role (user or assistant)
        
        Args:
            message: The latest message added to the conversation
        """
        # Get current mood's natural energy level
        mood_energy = MOODS.get(self.mood, MOODS[DEFAULT_MOOD]).get("energy", 3)
        
        # Base the new energy level on the current mood's energy
        new_energy = mood_energy
        
        # Analyze message content for energy indicators
        if message.role == "user":
            # User messages can boost energy
            content = message.content
            
            # Longer messages increase energy (slightly)
            if len(content) > 100:
                new_energy += 1
            
            # Excitement indicators
            exclamation_count = content.count('!')
            if exclamation_count > 2:
                new_energy += 1
            
            # CAPS increase energy
            caps_ratio = sum(1 for c in content if c.isupper()) / max(1, len(content))
            if caps_ratio > 0.3:  # If more than 30% is caps
                new_energy += 1
                
            # Questions may increase energy slightly
            if '?' in content:
                new_energy += 0.5
                
        # Gradually shift current energy toward the new target
        # This creates a "momentum" effect where energy changes gradually
        energy_diff = new_energy - self.energy_level
        self.energy_level += energy_diff * 0.3  # Only move 30% toward the target
        
        # Ensure energy stays within bounds (0-5)
        self.energy_level = max(0, min(5, self.energy_level))
        
    def get_energy_indicator(self) -> str:
        """
        Get the visual indicator for the current energy level.
        
        Returns:
            A string representation of the energy level
        """
        if not ENABLE_ENERGY_METER:
            return ""
            
        # Round to nearest integer for display
        energy_int = round(self.energy_level)
        return ENERGY_LEVEL_INDICATORS.get(energy_int, "⚡" * energy_int)
        
    def set_personality(self, personality_name: str) -> bool:
        """
        Set the personality for this conversation.
        
        Args:
            personality_name: Name of the personality to set
            
        Returns:
            True if successful, False if personality doesn't exist
        """
        if personality_name in PERSONALITIES:
            self.personality = personality_name
            return True
        return False
        
    def get_personality_params(self) -> dict:
        """
        Get the Gemini API parameters for the current personality.
        
        Returns:
            Dictionary of parameters to pass to the Gemini API
        """
        personality = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])
        return personality.get("gemini_params", {})
        
    def get_personality_emoji(self) -> str:
        """Get the emoji associated with the current personality."""
        personality = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])
        return personality.get("emoji", "")
        
    def get_personality_name(self) -> str:
        """Get the display name of the current personality."""
        personality = PERSONALITIES.get(self.personality, PERSONALITIES[DEFAULT_PERSONALITY])
        return personality.get("name", self.personality.capitalize())
    
    def get_formatted_history(self, include_all: bool = False) -> List[Dict[str, Any]]:
        """
        Get the conversation history formatted for the Gemini API.
        
        Args:
            include_all: Whether to include all messages (True) or just the most recent ones (False)
        
        Returns:
            List of messages in the format expected by Gemini API
        """
        if not self.messages:
            return []
        
        # If not including all, only return the most recent messages
        messages_to_include = self.messages if include_all else self.messages[-MAX_CONVERSATION_HISTORY:]
        
        return [
            {"role": msg.role, "parts": [{"text": msg.content}]}
            for msg in messages_to_include
        ]
    
    def get_preview(self, max_length: int = CONVERSATION_PREVIEW_LENGTH) -> List[Message]:
        """
        Get a preview of the most recent conversation messages.
        
        Args:
            max_length: Maximum number of messages to include in the preview
            
        Returns:
            List of the most recent messages
        """
        # Return at most the specified number of messages
        return self.messages[-min(max_length, len(self.messages)):]
    
    def is_expired(self) -> bool:
        """Check if the conversation has expired based on inactivity."""
        return time.time() - self.last_activity > CONVERSATION_MEMORY_EXPIRY
    
    def maybe_change_mood(self) -> str:
        """
        Possibly change the conversation mood based on probability.
        
        Returns:
            The current mood (which may have changed)
        """
        if not ENABLE_MOOD_INDICATOR:
            return DEFAULT_MOOD
            
        # Randomly change mood based on probability
        if random.random() < MOOD_CHANGE_PROBABILITY:
            available_moods = list(MOODS.keys())
            self.mood = random.choice(available_moods)
            logger.debug(f"Mood changed to: {self.mood}")
        
        return self.mood
    
    def get_mood_decorator(self) -> Tuple[str, str]:
        """
        Get prefix and suffix decorators based on the current mood.
        
        Returns:
            Tuple of (prefix, suffix) to apply to the message based on mood
        """
        if not ENABLE_MOOD_INDICATOR:
            return "", ""
            
        mood_info = MOODS.get(self.mood, MOODS[DEFAULT_MOOD])
        prefix = random.choice(mood_info["prefixes"]) if mood_info["prefixes"] else ""
        suffix = random.choice(mood_info["suffixes"]) if mood_info["suffixes"] else ""
        
        return prefix, suffix
    
    def get_mood_emoji(self) -> str:
        """Get the emoji associated with the current mood."""
        if not ENABLE_MOOD_INDICATOR:
            return ""
            
        return MOODS.get(self.mood, MOODS[DEFAULT_MOOD]).get("emoji", "")


# Optional database conversation support - only import if needed
try:
    from utils.db_conversation_adapter import DBConversationAdapter
    has_db_adapter = True
    logger.info("Database conversation adapter imported successfully")
except ImportError:
    has_db_adapter = False
    logger.warning("Could not import database conversation adapter - using in-memory only")

class ConversationManager:
    """Manages conversations for different users and channels."""
    
    def __init__(self):
        """Initialize the conversation manager."""
        # User conversations: {user_id: Conversation}
        self.user_conversations: Dict[int, Conversation] = {}
        
        # Channel conversations: {channel_id: Conversation}
        self.channel_conversations: Dict[int, Conversation] = {}
        
        # Regular cleanup interval (every hour)
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
        
        # Database adapter if available
        self.db_adapter = DBConversationAdapter() if has_db_adapter else None
        
        logger.info(f"Conversation manager initialized. Database support: {self.db_adapter is not None}")
    
    def get_user_conversation(self, user_id: int, username: str = "") -> Conversation:
        """
        Get or create a conversation for a user.
        
        Args:
            user_id: Discord user ID
            username: Discord username (optional)
            
        Returns:
            The user's conversation
        """
        # Clean up expired conversations periodically
        self._maybe_cleanup()
        
        # Check if we have a conversation in memory
        conversation = self.user_conversations.get(user_id)
        
        # If no conversation in memory, create one
        if not conversation:
            conversation = Conversation()
            self.user_conversations[user_id] = conversation
            
            # If we have a database adapter, load conversation from DB
            if self.db_adapter:
                try:
                    # Get conversation data from database
                    conv_props, messages = self.db_adapter.get_user_conversation(user_id, username)
                    
                    # Apply properties to conversation
                    conversation.mood = conv_props.get("mood", DEFAULT_MOOD)
                    conversation.personality = conv_props.get("personality", DEFAULT_PERSONALITY)
                    conversation.energy_level = conv_props.get("energy_level", 3)
                    
                    # Add messages to conversation if any
                    for msg in messages:
                        message = Message(
                            role=msg["role"],
                            content=msg["parts"][0]["text"],
                            author_name=username if msg["role"] == "user" else "Gemini"
                        )
                        conversation.messages.append(message)
                        
                    logger.debug(f"Loaded conversation for user {user_id} from database: {len(messages)} messages")
                except Exception as e:
                    logger.error(f"Error loading conversation from database: {e}")
        
        return conversation
    
    def get_channel_conversation(self, channel_id: int, channel_name: str = "") -> Conversation:
        """
        Get or create a conversation for a channel.
        
        Args:
            channel_id: Discord channel ID
            channel_name: Channel name (optional)
            
        Returns:
            The channel's conversation
        """
        # Clean up expired conversations periodically
        self._maybe_cleanup()
        
        # Check if we have a conversation in memory
        conversation = self.channel_conversations.get(channel_id)
        
        # If no conversation in memory, create one
        if not conversation:
            conversation = Conversation()
            self.channel_conversations[channel_id] = conversation
            
            # If we have a database adapter, load conversation from DB
            if self.db_adapter:
                try:
                    # Get conversation data from database
                    conv_props, messages = self.db_adapter.get_channel_conversation(channel_id, channel_name)
                    
                    # Apply properties to conversation
                    conversation.mood = conv_props.get("mood", DEFAULT_MOOD)
                    conversation.personality = conv_props.get("personality", DEFAULT_PERSONALITY)
                    conversation.energy_level = conv_props.get("energy_level", 3)
                    
                    # Add messages to conversation if any
                    for msg in messages:
                        message = Message(
                            role=msg["role"],
                            content=msg["parts"][0]["text"],
                            author_name="User" if msg["role"] == "user" else "Gemini"
                        )
                        conversation.messages.append(message)
                        
                    logger.debug(f"Loaded conversation for channel {channel_id} from database: {len(messages)} messages")
                except Exception as e:
                    logger.error(f"Error loading channel conversation from database: {e}")
        
        return conversation
    
    def add_user_message(self, user_id: int, content: str, author_name: str = "") -> None:
        """
        Add a user message to their conversation history.
        
        Args:
            user_id: Discord user ID
            content: Message content
            author_name: Name of the user
        """
        # Get the conversation
        conversation = self.get_user_conversation(user_id, author_name)
        
        # Create message
        message = Message(
            role="user",
            content=content,
            author_name=author_name,
            author_id=user_id
        )
        
        # Add to in-memory conversation
        conversation.add_message(message)
        
        # Also add to database if available
        if self.db_adapter:
            try:
                self.db_adapter.add_user_message(user_id, content, author_name)
            except Exception as e:
                logger.error(f"Error saving user message to database: {e}")
    
    def add_assistant_message(self, user_id: int, content: str) -> None:
        """
        Add an assistant's response to a user's conversation history.
        
        Args:
            user_id: Discord user ID
            content: Message content
        """
        # Get the conversation
        conversation = self.get_user_conversation(user_id)
        
        # Create message
        message = Message(
            role="assistant",
            content=content,
            author_name="Gemini",
            author_id=0  # 0 for the bot itself
        )
        
        # Add to in-memory conversation
        conversation.add_message(message)
        
        # Also add to database if available
        if self.db_adapter:
            try:
                self.db_adapter.add_assistant_message(user_id, content)
            except Exception as e:
                logger.error(f"Error saving assistant message to database: {e}")
    
    def add_channel_user_message(self, channel_id: int, user_id: int, content: str, author_name: str = "") -> None:
        """
        Add a user message to a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            user_id: Discord user ID
            content: Message content
            author_name: Name of the user
        """
        # Get the conversation
        conversation = self.get_channel_conversation(channel_id)
        
        # Create message
        message = Message(
            role="user",
            content=content,
            author_name=author_name,
            author_id=user_id
        )
        
        # Add to in-memory conversation
        conversation.add_message(message)
        
        # Also add to database if available
        if self.db_adapter:
            try:
                self.db_adapter.add_channel_user_message(channel_id, user_id, content, author_name)
            except Exception as e:
                logger.error(f"Error saving channel user message to database: {e}")
    
    def add_channel_assistant_message(self, channel_id: int, content: str) -> None:
        """
        Add an assistant's response to a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            content: Message content
        """
        # Get the conversation
        conversation = self.get_channel_conversation(channel_id)
        
        # Create message
        message = Message(
            role="assistant",
            content=content,
            author_name="Gemini",
            author_id=0  # 0 for the bot itself
        )
        
        # Add to in-memory conversation
        conversation.add_message(message)
        
        # Also add to database if available
        if self.db_adapter:
            try:
                self.db_adapter.add_channel_assistant_message(channel_id, content)
            except Exception as e:
                logger.error(f"Error saving channel assistant message to database: {e}")
    
    def clear_user_conversation(self, user_id: int) -> bool:
        """
        Clear a user's conversation history.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if the conversation was cleared, False if it didn't exist
        """
        success = False
        
        # Clear in-memory conversation
        if user_id in self.user_conversations:
            self.user_conversations[user_id] = Conversation()
            success = True
        
        # Also clear in database if available
        if self.db_adapter:
            try:
                db_success = self.db_adapter.clear_user_conversation(user_id)
                success = success or db_success
                if db_success:
                    logger.debug(f"Cleared conversation history for user {user_id} in database")
            except Exception as e:
                logger.error(f"Error clearing user conversation in database: {e}")
        
        return success
    
    def clear_channel_conversation(self, channel_id: int) -> bool:
        """
        Clear a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            True if the conversation was cleared, False if it didn't exist
        """
        success = False
        
        # Clear in-memory conversation
        if channel_id in self.channel_conversations:
            self.channel_conversations[channel_id] = Conversation()
            success = True
        
        # Also clear in database if available
        if self.db_adapter:
            try:
                db_success = self.db_adapter.clear_channel_conversation(channel_id)
                success = success or db_success
                if db_success:
                    logger.debug(f"Cleared conversation history for channel {channel_id} in database")
            except Exception as e:
                logger.error(f"Error clearing channel conversation in database: {e}")
        
        return success
    
    def get_user_conversation_preview(self, user_id: int) -> Optional[List[Message]]:
        """
        Get a preview of a user's recent conversation.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            List of recent messages or None if no conversation exists
        """
        if user_id in self.user_conversations:
            return self.user_conversations[user_id].get_preview()
        return None
    
    def get_channel_conversation_preview(self, channel_id: int) -> Optional[List[Message]]:
        """
        Get a preview of a channel's recent conversation.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            List of recent messages or None if no conversation exists
        """
        if channel_id in self.channel_conversations:
            return self.channel_conversations[channel_id].get_preview()
        return None
    
    def format_preview_for_discord(self, messages: List[Message]) -> str:
        """
        Format conversation preview messages for display in Discord.
        
        Args:
            messages: List of messages to format
            
        Returns:
            Formatted string for display
        """
        if not messages:
            return "*No recent conversation.*"
        
        formatted = ["**Conversation Preview:**"]
        
        for msg in messages:
            name = msg.author_name or ("You" if msg.role == "user" else "Gemini")
            formatted.append(f"**{name}**: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
        
        return "\n".join(formatted)
        
    def set_user_personality(self, user_id: int, personality_name: str) -> bool:
        """
        Set the personality for a user's conversation.
        
        Args:
            user_id: Discord user ID
            personality_name: Name of the personality to set
            
        Returns:
            True if the personality was set successfully, False otherwise
        """
        # Get the user's conversation
        conversation = self.get_user_conversation(user_id)
        in_memory_success = conversation.set_personality(personality_name)
        
        # If successfully set in memory, also set in database if available
        if in_memory_success and self.db_adapter:
            try:
                db_success = self.db_adapter.set_user_personality(user_id, personality_name)
                if not db_success:
                    logger.warning(f"Failed to set personality '{personality_name}' for user {user_id} in database")
            except Exception as e:
                logger.error(f"Error setting personality in database: {e}")
        
        return in_memory_success
        
    def get_user_personality(self, user_id: int) -> str:
        """
        Get the personality for a user's conversation.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            The name of the user's current personality, or the default personality if none set
        """
        # Check if we have a database personality setting
        personality = None
        if self.db_adapter:
            try:
                personality = self.db_adapter.get_user_personality(user_id)
            except Exception as e:
                logger.error(f"Error getting personality from database: {e}")
        
        # If no database personality, use in-memory conversation
        if not personality:
            conversation = self.get_user_conversation(user_id)
            personality = conversation.personality
        
        return personality
    
    def _maybe_cleanup(self) -> None:
        """Periodically clean up expired conversations to free memory."""
        current_time = time.time()
        
        # Only run cleanup at the specified interval
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        # Update cleanup timestamp
        self.last_cleanup = current_time
        
        # Clean up user conversations
        expired_user_ids = [
            user_id for user_id, conversation in self.user_conversations.items()
            if conversation.is_expired()
        ]
        
        for user_id in expired_user_ids:
            del self.user_conversations[user_id]
        
        # Clean up channel conversations
        expired_channel_ids = [
            channel_id for channel_id, conversation in self.channel_conversations.items()
            if conversation.is_expired()
        ]
        
        for channel_id in expired_channel_ids:
            del self.channel_conversations[channel_id]
        
        if expired_user_ids or expired_channel_ids:
            logger.info(
                f"Cleaned up {len(expired_user_ids)} expired user conversations and "
                f"{len(expired_channel_ids)} expired channel conversations"
            )


# Create a singleton conversation manager instance
conversation_manager = ConversationManager()

class GeminiAIService:
    """Service for interacting with the Gemini AI API."""
    
    def __init__(self):
        """Initialize the Gemini AI service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.critical("GEMINI_API_KEY not found in environment variables.")
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Store the model and configuration
        self.model_name = GEMINI_MODEL
        self.generation_config = {
            "max_output_tokens": GEMINI_MAX_TOKENS,
            "temperature": GEMINI_TEMPERATURE,
            "top_p": GEMINI_TOP_P,
            "top_k": GEMINI_TOP_K
        }
        
        # System instructions for the AI
        self.system_instructions = GEMINI_SYSTEM_INSTRUCTIONS
        
        logger.info(f"Initialized Gemini AI service with model: {self.model_name}")
    
    async def generate_response(self, prompt: str, user_id: Optional[int] = None, 
                               channel_id: Optional[int] = None, author_name: str = "") -> Tuple[str, Optional[Any]]:
        """
        Generate a response from Gemini 1.5 based on the given prompt.
        
        Args:
            prompt: The text prompt to send to the AI.
            user_id: Optional Discord user ID for conversation memory.
            channel_id: Optional Discord channel ID for conversation memory.
            author_name: Name of the user sending the prompt.
            
        Returns:
            A tuple containing (response_text, conversation_object).
        """
        try:
            conversation_preview = None
            conversation_history = None
            mood_prefix = ""
            mood_suffix = ""
            mood_emoji = ""
            personality_params = {}
            energy_indicator = ""
            personality_emoji = ""
            
            # Handle conversation memory if enabled
            if ENABLE_CONVERSATION_MEMORY:
                if user_id:
                    # User-specific conversation
                    conversation = conversation_manager.get_user_conversation(user_id)
                    conversation_manager.add_user_message(user_id, prompt, author_name)
                    conversation_history = conversation.get_formatted_history()
                    conversation_preview = conversation_manager.get_user_conversation_preview(user_id)
                    
                    # Get mood information if enabled
                    if ENABLE_MOOD_INDICATOR:
                        conversation.maybe_change_mood()
                        mood_prefix, mood_suffix = conversation.get_mood_decorator()
                        mood_emoji = conversation.get_mood_emoji()
                    
                    # Get energy indicator if enabled
                    if ENABLE_ENERGY_METER:
                        energy_indicator = conversation.get_energy_indicator()
                    
                    # Get personality parameters
                    personality_params = conversation.get_personality_params()
                    personality_emoji = conversation.get_personality_emoji()
                        
                elif channel_id:
                    # Channel-specific conversation
                    conversation = conversation_manager.get_channel_conversation(channel_id)
                    conversation_manager.add_channel_user_message(channel_id, user_id or 0, prompt, author_name)
                    conversation_history = conversation.get_formatted_history()
                    conversation_preview = conversation_manager.get_channel_conversation_preview(channel_id)
                    
                    # Get mood information if enabled
                    if ENABLE_MOOD_INDICATOR:
                        conversation.maybe_change_mood()
                        mood_prefix, mood_suffix = conversation.get_mood_decorator()
                        mood_emoji = conversation.get_mood_emoji()
                    
                    # Get energy indicator if enabled
                    if ENABLE_ENERGY_METER:
                        energy_indicator = conversation.get_energy_indicator()
                    
                    # Get personality parameters
                    personality_params = conversation.get_personality_params()
                    personality_emoji = conversation.get_personality_emoji()
            
            # Create a generative model instance with personality parameters
            generation_config = self.generation_config.copy()
            
            # Apply personality parameters if available
            if personality_params:
                for param, value in personality_params.items():
                    generation_config[param] = value
            
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )
            
            # Prepare the content for the model based on whether we have conversation history
            if conversation_history:
                # Note: Gemini 1.5 doesn't support system role, use user message with instructions
                instructions_message = {"role": "user", "parts": [{"text": f"Instructions for you: {self.system_instructions}"}]}
                
                # Make sure none of the messages use "system" role
                sanitized_history = []
                for msg in conversation_history:
                    # If role is "system", change it to "user"
                    msg_copy = msg.copy()
                    if msg_copy["role"] == "system":
                        msg_copy["role"] = "user"
                    sanitized_history.append(msg_copy)
                
                conversation_with_instructions = [instructions_message] + sanitized_history
                
                # Use conversation history to generate a contextual response
                response = await asyncio.to_thread(
                    model.generate_content,
                    conversation_with_instructions
                )
            else:
                # No conversation history, use structured messages
                messages = [
                    {"role": "user", "parts": [{"text": f"Instructions for you: {self.system_instructions}"}]},
                    {"role": "user", "parts": [{"text": prompt}]}
                ]
                response = await asyncio.to_thread(
                    model.generate_content,
                    messages
                )
            
            # Extract the text from the response
            if hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response.candidates[0].content.parts[0].text)
            
            # Build styled response with mood, energy, and personality indicators
            styled_response = response_text
            
            # Start with base response text
            prefix_parts = []
            suffix_parts = []
            
            # Add mood styling if enabled
            if ENABLE_MOOD_INDICATOR and (mood_prefix or mood_suffix or mood_emoji):
                if mood_emoji:
                    prefix_parts.append(f"{mood_emoji}")
                if mood_prefix:
                    prefix_parts.append(mood_prefix)
                if mood_suffix:
                    suffix_parts.append(mood_suffix)
                    
            # Add energy meter if enabled
            if ENABLE_ENERGY_METER and energy_indicator:
                suffix_parts.append(f" {energy_indicator}")
                
            # Add personality indicator if available
            if personality_emoji:
                prefix_parts.append(f"{personality_emoji}")
                
            # Combine everything
            prefix = " ".join(prefix_parts) + " " if prefix_parts else ""
            suffix = " " + " ".join(suffix_parts) if suffix_parts else ""
            
            styled_response = f"{prefix}{response_text}{suffix}"
            
            # Store the assistant's response in conversation memory if enabled
            if ENABLE_CONVERSATION_MEMORY:
                if user_id:
                    conversation_manager.add_assistant_message(user_id, response_text)
                elif channel_id:
                    conversation_manager.add_channel_assistant_message(channel_id, response_text)
            
            # Return the styled response and the conversation object
            if ENABLE_CONVERSATION_MEMORY:
                if user_id:
                    return styled_response, conversation
                elif channel_id:
                    return styled_response, conversation
            
            # If conversation memory is not enabled, return None for the conversation
            return styled_response, None
                
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            raise Exception(f"Failed to generate AI response: {str(e)}")
    
    async def clear_conversation(self, user_id: Optional[int] = None, channel_id: Optional[int] = None) -> bool:
        """
        Clear conversation history for a user or channel.
        
        Args:
            user_id: Optional Discord user ID.
            channel_id: Optional Discord channel ID.
        
        Returns:
            True if the conversation was cleared, False otherwise.
        """
        if user_id:
            return conversation_manager.clear_user_conversation(user_id)
        elif channel_id:
            return conversation_manager.clear_channel_conversation(channel_id)
        return False
    
    async def get_conversation_preview(self, user_id: Optional[int] = None, channel_id: Optional[int] = None) -> Optional[str]:
        """
        Get the conversation preview for a user or channel.
        
        Args:
            user_id: Optional Discord user ID.
            channel_id: Optional Discord channel ID.
        
        Returns:
            Formatted conversation preview string or None if no conversation exists.
        """
        preview = None
        
        if user_id:
            preview = conversation_manager.get_user_conversation_preview(user_id)
        elif channel_id:
            preview = conversation_manager.get_channel_conversation_preview(channel_id)
        
        if preview:
            return conversation_manager.format_preview_for_discord(preview)
        
        return None

class AICommands(commands.Cog, name="AI Commands"):
    """Commands for interacting with Gemini AI."""
    
    def __init__(self, bot):
        """Initialize the AI commands cog."""
        self.bot = bot
        self.ai_service = GeminiAIService()
        
        # Command cooldowns
        self.cooldowns = commands.CooldownMapping.from_cooldown(
            1, COMMAND_COOLDOWN, commands.BucketType.user
        )
        
        logger.info("AI commands cog initialized")
    
    @commands.command()
    async def ask(self, ctx, *, prompt: str):
        """
        Ask Gemini AI a question or provide a prompt.
        
        Usage: !ask <your question or prompt>
        
        Add [embed] to your question to force the response in a rich embed format.
        Reply to another message to provide additional context.
        """
        # Apply cooldown
        bucket = self.cooldowns.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            await ctx.send(f"Please wait {retry_after:.1f}s before using this command again.")
            return
        
        # Check if the message is a reply to a previous message for context awareness
        referenced_message = ctx.message.reference.resolved if ctx.message.reference else None
        context_message = None
        is_context_aware = False
        
        # If this is a reply to a previous message, add context awareness
        if referenced_message and not referenced_message.author.bot:
            # Get the message being replied to for context
            context_message = f"[Replying to {referenced_message.author.display_name}: \"{referenced_message.content}\"]"
            is_context_aware = True
        
        # Show typing indicator
        async with ctx.typing():
            try:
                # Show thinking message
                thinking_msg = await ctx.send("🧠 *Thinking...*")
                
                # Get user information for conversation memory
                user_id = ctx.author.id if ENABLE_CONVERSATION_MEMORY else None
                author_name = ctx.author.display_name
                
                # Construct the prompt with context if applicable
                full_prompt = prompt
                if context_message:
                    full_prompt = f"{context_message}\n\n{prompt}"
                
                # Generate the AI response with conversation memory
                response, conversation = await self.ai_service.generate_response(
                    full_prompt, 
                    user_id=user_id,
                    author_name=author_name
                )
                
                # Add footer if not too long
                if len(response) + len(RESPONSE_FOOTER) <= MAX_RESPONSE_LENGTH:
                    response += RESPONSE_FOOTER
                
                # Delete thinking message
                await thinking_msg.delete()
                
                # Determine if we should use advanced formatting (embed)
                # Use embeds for responses containing code blocks, long explanations, or when requested
                use_embed = (
                    "```" in response or  # Code blocks
                    len(response) > 500 or  # Long responses
                    "[embed]" in prompt.lower() or  # Explicitly requested
                    (is_context_aware and len(response) > 200)  # Context-aware and moderately long
                )
                
                # If response is too long, always use embed or split into chunks
                if len(response) > MAX_RESPONSE_LENGTH:
                    if "```" in response or is_context_aware:
                        # For code blocks or context-aware replies, prefer embeds
                        use_embed = True
                
                # Get mood and personality indicators if enabled
                mood_emoji = conversation.get_mood_emoji() if conversation else ""
                personality_emoji = conversation.get_personality_emoji() if conversation else ""
                energy_indicator = conversation.get_energy_indicator() if conversation else ""
                
                # For embeds, prepare a rich embed with formatting
                if use_embed:
                    embed = discord.Embed(
                        description=response[:4000],  # Embed description has 4000 char limit
                        color=0x4285F4  # Google Blue
                    )
                    
                    # Add custom title based on context
                    if is_context_aware:
                        embed.title = f"Reply to: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                    else:
                        embed.title = f"Response to: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                    
                    # Add personality and mood indicators in footer
                    footer_text = ""
                    if personality_emoji:
                        footer_text += f"{personality_emoji} "
                    if mood_emoji:
                        footer_text += f"{mood_emoji} "
                    if energy_indicator:
                        footer_text += f"{energy_indicator} "
                    
                    footer_text += "Powered by Gemini 1.5 AI"
                    embed.set_footer(text=footer_text)
                    
                    # Send the embed
                    await ctx.send(embed=embed)
                    
                    # If response was too long for the embed, send remaining text as regular messages
                    if len(response) > 4000:
                        remaining_chunks = [response[4000:][i:i+MAX_RESPONSE_LENGTH] 
                                        for i in range(0, len(response[4000:]), MAX_RESPONSE_LENGTH)]
                        for chunk in remaining_chunks:
                            await ctx.send(chunk)
                else:
                    # Add mood/personality indicators
                    if mood_emoji or personality_emoji or energy_indicator:
                        indicator = f"{mood_emoji} {personality_emoji} {energy_indicator}".strip()
                        if indicator:
                            response = f"{indicator} {response}"
                    
                    # Split response if too long
                    if len(response) > MAX_RESPONSE_LENGTH:
                        chunks = [response[i:i+MAX_RESPONSE_LENGTH] 
                                for i in range(0, len(response), MAX_RESPONSE_LENGTH)]
                        
                        # Send chunks
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        # Send complete response
                        await ctx.send(response)
                
                # If we have a conversation and the user has a conversation history, send it as an embed
                if conversation and hasattr(conversation, 'messages') and len(conversation.messages) > 1:
                    # Get a preview of the conversation
                    conversation_preview = ""
                    for i, msg in enumerate(conversation.get_preview()):
                        if i >= 5:  # Show at most 5 messages
                            break
                        role_emoji = "👤" if msg.role == "user" else "🤖"
                        name = msg.author_name if msg.author_name else ("You" if msg.role == "user" else "Gemini")
                        # Truncate long messages in the preview
                        content = msg.content[:100] + ("..." if len(msg.content) > 100 else "")
                        # Add to the preview
                        conversation_preview += f"{role_emoji} **{name}**: {content}\n\n"
                    
                    # Only send the preview privately (ephemeral) to the command user
                    if conversation_preview:
                        embed = discord.Embed(
                            title="Your Conversation Context",
                            description=conversation_preview,
                            color=discord.Color.blue()
                        )
                        embed.set_footer(text="This is what I remember from our conversation.")
                        
                        # Try to send the preview as a DM to avoid cluttering the channel
                        try:
                            await ctx.author.send(embed=embed)
                        except discord.Forbidden:
                            # If DM fails, just skip it - avoid cluttering the channel
                            pass
                    
            except Exception as e:
                # Delete thinking message if it exists
                try:
                    await thinking_msg.delete()
                except:
                    pass
                
                logger.error(f"Error in ask command: {e}")
                await ctx.send(f"Sorry, I encountered an error: {str(e)}")
    
    @commands.command()
    async def set_personality(self, ctx, personality_name: str = None):
        """
        Set the AI personality for your conversations.
        
        Available personalities: balanced, creative, precise, friendly, technical
        
        Usage: !set_personality <personality_name>
        Example: !set_personality creative
        """
        if not USER_SELECTABLE_PERSONALITY:
            await ctx.send("Personality selection is not enabled. Contact the bot administrator.")
            return
            
        if not personality_name:
            # Show available personalities
            personalities_list = []
            for p_id, p_info in PERSONALITIES.items():
                emoji = p_info.get("emoji", "")
                name = p_info.get("name", p_id.capitalize())
                description = p_info.get("description", "")
                personalities_list.append(f"{emoji} **{name}**: {description}")
            
            embed = discord.Embed(
                title="Available Personalities",
                description="Choose a personality with `!set_personality <name>`",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Options",
                value="\n".join(personalities_list),
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
            
        # Get user conversation
        if not ENABLE_CONVERSATION_MEMORY:
            await ctx.send("Conversation memory is disabled, so personalities cannot be set.")
            return
            
        user_id = ctx.author.id
        conversation = conversation_manager.get_user_conversation(user_id)
        
        # Try to set the personality
        personality_name = personality_name.lower()
        if personality_name not in PERSONALITIES:
            await ctx.send(f"Unknown personality: '{personality_name}'. Use `!set_personality` to see available options.")
            return
            
        # Set the personality using conversation manager to save to DB
        success = conversation_manager.set_user_personality(user_id, personality_name)
        
        if success:
            personality = PERSONALITIES[personality_name]
            emoji = personality.get("emoji", "")
            name = personality.get("name", personality_name.capitalize())
            
            await ctx.send(f"{emoji} Personality set to **{name}**! Your future interactions will use this personality.")
        else:
            await ctx.send("Failed to set personality. Please try again.")
    
    @commands.command()
    async def about(self, ctx):
        """Show information about the Gemini AI bot."""
        embed = discord.Embed(
            title="About Gemini 1.5 AI Bot",
            description="This bot is powered by Google's Gemini 1.5 AI model.",
            color=discord.Color.blue()
        )
        
        # Add usage info
        embed.add_field(
            name="Usage",
            value=(
                "**Ask a question**: `!ask <your question>`\n"
                "**Advanced formatting**: `!ask [embed] <your question>`\n"
                "**Context-aware**: Reply to a message when using `!ask`\n"
                "**Set personality**: `!set_personality <personality_name>`\n"
                "**Get help**: `!help`\n"
                "**About**: `!about`"
            ),
            inline=False
        )
        
        # Add features info
        embed.add_field(
            name="Features",
            value=(
                "• Natural language understanding\n"
                "• Multi-language support\n"
                "• Contextual conversation memory\n"
                "• Context-aware replies and message threading\n"
                "• Rich embed formatting for code and longer responses\n"
                "• Auto-response in designated channels\n"
                "• AI with mood indicators and personalities\n"
                "• Energy level meters that adapt to conversation"
            ),
            inline=False
        )
        
        # Add technical details
        embed.add_field(
            name="Technical Details",
            value=(
                f"**Model**: {GEMINI_MODEL}\n"
                f"**Conversation Memory**: {'Enabled' if ENABLE_CONVERSATION_MEMORY else 'Disabled'}\n"
                f"**Mood Indicators**: {'Enabled' if ENABLE_MOOD_INDICATOR else 'Disabled'}\n"
                f"**Energy Meter**: {'Enabled' if ENABLE_ENERGY_METER else 'Disabled'}\n"
                f"**User Personalities**: {'Enabled' if USER_SELECTABLE_PERSONALITY else 'Disabled'}"
            ),
            inline=False
        )
        
        # Add auto-response channels if configured
        if AUTO_RESPONSE_CHANNELS:
            channels_text = "\n".join([f"<#{channel_id}>" for channel_id in AUTO_RESPONSE_CHANNELS])
            embed.add_field(
                name="Auto-Response Channels",
                value=channels_text,
                inline=False
            )
        
        embed.set_footer(text="Powered by Gemini 1.5 AI")
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages in auto-response channels and direct messages."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if this is a valid channel for auto-response
        is_auto_channel = message.channel.id in AUTO_RESPONSE_CHANNELS
        is_direct_message = isinstance(message.channel, discord.DMChannel) and ENABLE_DIRECT_MESSAGE_RESPONSES
        
        # Skip if not in an auto-response channel or DM
        if not is_auto_channel and not is_direct_message:
            return
        
        # Check if message starts with an ignored prefix
        for prefix in AUTO_RESPONSE_IGNORE_PREFIX:
            if message.content.startswith(prefix):
                return
        
        # Apply user-specific, channel-specific, and combined rate limiting
        user_id = message.author.id
        channel_id = message.channel.id
        user_channel_key = f"{user_id}:{channel_id}"
        current_time = time.time()
        
        # Check user-specific cooldown first
        if user_id in user_cooldowns:
            time_diff = current_time - user_cooldowns[user_id]
            if time_diff < AUTO_RESPONSE_COOLDOWN:
                # Add reaction if message came quickly after the last one
                if time_diff < 2:
                    try:
                        await message.add_reaction("⏳")
                        # Provide feedback about remaining cooldown
                        cooldown_remaining = round(AUTO_RESPONSE_COOLDOWN - time_diff)
                        if cooldown_remaining > 2:  # Only DM if more than 2 seconds remaining
                            try:
                                await message.author.send(f"Please wait {cooldown_remaining} more seconds before I can respond again.")
                            except discord.Forbidden:
                                pass  # Can't DM the user, just skip
                    except discord.Forbidden:
                        pass
                return
                
        # Also check channel cooldown (to prevent spam in a single channel)
        if channel_id in channel_cooldowns:
            time_diff = current_time - channel_cooldowns[channel_id]
            if time_diff < (AUTO_RESPONSE_COOLDOWN / 2):  # Channel cooldown is half the user cooldown
                # If channel hit rate limit but user didn't, just ignore silently
                return
        
        # Check combined user+channel cooldown (stricter limits for same user in same channel)
        if user_channel_key in user_channel_cooldowns:
            time_diff = current_time - user_channel_cooldowns[user_channel_key]
            if time_diff < (AUTO_RESPONSE_COOLDOWN * 1.5):  # 50% longer cooldown for repeated usage in same channel
                # Add reaction if message came quickly after the last one
                if time_diff < 3:
                    try:
                        await message.add_reaction("⏳")
                    except discord.Forbidden:
                        pass
                return
                
        # Update all cooldowns
        user_cooldowns[user_id] = current_time
        channel_cooldowns[channel_id] = current_time
        user_channel_cooldowns[user_channel_key] = current_time
        
        # Check if the message is a reply to a previous message
        referenced_message = message.reference.resolved if message.reference else None
        context_message = None
        is_context_aware = False
        
        # If this is a reply to a previous message, add context awareness
        if referenced_message and not referenced_message.author.bot:
            # Get the message being replied to for context
            context_message = f"[Replying to {referenced_message.author.display_name}: \"{referenced_message.content}\"]"
            is_context_aware = True
        
        # Process the message
        async with message.channel.typing():
            try:
                # Get user information for conversation memory
                author_id = message.author.id if ENABLE_CONVERSATION_MEMORY else None
                channel_id = message.channel.id if ENABLE_CONVERSATION_MEMORY else None
                author_name = message.author.display_name
                
                # Construct the prompt with context if applicable
                prompt = message.content
                if context_message:
                    prompt = f"{context_message}\n\n{prompt}"
                
                # Generate the AI response with conversation memory (preferring channel conversation over user)
                response, conversation = await self.ai_service.generate_response(
                    prompt,
                    channel_id=channel_id,
                    user_id=author_id,
                    author_name=author_name
                )
                
                # Add footer if not too long
                if len(response) + len(RESPONSE_FOOTER) <= MAX_RESPONSE_LENGTH:
                    response += RESPONSE_FOOTER
                
                # Determine if we should use advanced formatting (embed)
                # Use embeds for responses containing code blocks, long explanations, or when requested
                use_embed = (
                    "```" in response or  # Code blocks
                    len(response) > 500 or  # Long responses
                    "[embed]" in message.content.lower() or  # Explicitly requested
                    (is_context_aware and len(response) > 200)  # Context-aware and moderately long
                )
                
                # If response is too long, always use embed or split into chunks
                if len(response) > MAX_RESPONSE_LENGTH:
                    if "```" in response or is_context_aware:
                        # For code blocks or context-aware replies, prefer embeds
                        use_embed = True
                        
                # Generate mood and personality indicators if enabled
                mood_emoji = conversation.get_mood_emoji() if conversation else ""
                personality_emoji = conversation.get_personality_emoji() if conversation else ""
                energy_indicator = conversation.get_energy_indicator() if conversation else ""
                
                # For embeds, prepare a rich embed with formatting
                if use_embed:
                    embed = discord.Embed(
                        description=response[:4000],  # Embed description has 4000 char limit
                        color=0x4285F4  # Google Blue
                    )
                    
                    # Add custom title based on context
                    if is_context_aware:
                        embed.title = f"Reply to {referenced_message.author.display_name}"
                    else:
                        embed.title = f"Response to {message.author.display_name}"
                    
                    # Add personality and mood indicators in footer
                    footer_text = ""
                    if personality_emoji:
                        footer_text += f"{personality_emoji} "
                    if mood_emoji:
                        footer_text += f"{mood_emoji} "
                    if energy_indicator:
                        footer_text += f"{energy_indicator} "
                    
                    footer_text += "Powered by Gemini 1.5 AI"
                    embed.set_footer(text=footer_text)
                    
                    # Send the embed as a reply
                    await message.reply(embed=embed)
                    
                    # If response was too long for the embed, send remaining text as regular messages
                    if len(response) > 4000:
                        remaining_chunks = [response[4000:][i:i+MAX_RESPONSE_LENGTH] 
                                          for i in range(0, len(response[4000:]), MAX_RESPONSE_LENGTH)]
                        for chunk in remaining_chunks:
                            await message.channel.send(chunk)
                else:
                    # Split response if too long
                    if len(response) > MAX_RESPONSE_LENGTH:
                        chunks = [response[i:i+MAX_RESPONSE_LENGTH] 
                                  for i in range(0, len(response), MAX_RESPONSE_LENGTH)]
                        
                        # Add mood/personality indicators to first chunk
                        first_chunk = chunks[0]
                        if mood_emoji or personality_emoji:
                            indicator = f"{mood_emoji} {personality_emoji} {energy_indicator}".strip()
                            if indicator:
                                first_chunk = f"{indicator} {first_chunk}"
                        
                        # Send first chunk as reply
                        await message.reply(first_chunk)
                        
                        # Send rest as regular messages
                        for chunk in chunks[1:]:
                            await message.channel.send(chunk)
                    else:
                        # Add mood/personality indicators
                        if mood_emoji or personality_emoji:
                            indicator = f"{mood_emoji} {personality_emoji} {energy_indicator}".strip()
                            if indicator:
                                response = f"{indicator} {response}"
                        
                        # Send as reply
                        await message.reply(response)
            
            except Exception as e:
                logger.error(f"Error in auto-response: {e}")
                await message.channel.send(f"Sorry, I encountered an error: {str(e)}")

class AdminCommands(commands.Cog, name="Admin Commands"):
    """Administrative commands for managing the bot."""
    
    def __init__(self, bot):
        """Initialize the admin commands cog."""
        self.bot = bot
        self.ai_service = GeminiAIService()
    
    async def cog_check(self, ctx):
        """Check if the user can use admin commands."""
        # Bot owners can always use admin commands
        if ctx.author.id in BOT_OWNERS:
            return True
        
        # Check if the user has the admin role
        if isinstance(ctx.author, discord.Member):
            admin_role = discord.utils.get(ctx.author.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                return True
        
        # User doesn't have permission
        await ctx.send("You don't have permission to use this command. Admin commands require the "
                      f"'{ADMIN_ROLE_NAME}' role or being a bot owner.")
        return False
    
    @commands.command()
    async def clear_history(self, ctx, target_type: str = None, target_id: Optional[int] = None):
        """
        Clear conversation history for a user or channel.
        
        Usage:
        !clear_history user @user - Clear a specific user's conversation history
        !clear_history channel #channel - Clear a specific channel's conversation history
        !clear_history channel - Clear the current channel's conversation history
        
        Requires the Bot Admin role or being a bot owner.
        """
        if not target_type:
            await ctx.send("Please specify what type of history to clear ('user' or 'channel').")
            return
        
        target_type = target_type.lower()
        
        if target_type not in ["user", "channel"]:
            await ctx.send("Invalid target type. Please use 'user' or 'channel'.")
            return
        
        # Handle user history clearing
        if target_type == "user":
            # If a user is mentioned, use that user's ID
            if ctx.message.mentions:
                user = ctx.message.mentions[0]
                user_id = user.id
                user_name = user.display_name
            # If a user ID is provided, use that
            elif target_id:
                user = self.bot.get_user(target_id)
                user_id = target_id
                user_name = user.display_name if user else f"User {target_id}"
            else:
                await ctx.send("Please mention a user or provide a user ID.")
                return
            
            # Clear the user's conversation history
            success = await self.ai_service.clear_conversation(user_id=user_id)
            
            if success:
                await ctx.send(f"✅ Conversation history cleared for {user_name}.")
            else:
                await ctx.send(f"No conversation history found for {user_name}.")
        
        # Handle channel history clearing
        elif target_type == "channel":
            # If a channel is mentioned, use that channel's ID
            if ctx.message.channel_mentions:
                channel = ctx.message.channel_mentions[0]
                channel_id = channel.id
                channel_name = channel.name
            # If a channel ID is provided, use that
            elif target_id:
                channel = self.bot.get_channel(target_id)
                channel_id = target_id
                channel_name = channel.name if channel else f"Channel {target_id}"
            # Otherwise, use the current channel
            else:
                channel = ctx.channel
                channel_id = channel.id
                channel_name = channel.name
            
            # Clear the channel's conversation history
            success = await self.ai_service.clear_conversation(channel_id=channel_id)
            
            if success:
                await ctx.send(f"✅ Conversation history cleared for #{channel_name}.")
            else:
                await ctx.send(f"No conversation history found for #{channel_name}.")
    
    @commands.command()
    async def botinfo(self, ctx):
        """Show detailed information about the bot (admin only)."""
        embed = discord.Embed(
            title=f"{self.bot.user.name} Bot Information",
            description="Detailed bot information and statistics",
            color=discord.Color.blue()
        )
        
        # Add general information
        embed.add_field(
            name="General",
            value=(
                f"**ID**: {self.bot.user.id}\n"
                f"**Created**: {self.bot.user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"**Servers**: {len(self.bot.guilds)}\n"
                f"**Status**: Online"
            ),
            inline=False
        )
        
        # Add current configuration
        embed.add_field(
            name="Configuration",
            value=(
                f"**Model**: {GEMINI_MODEL}\n"
                f"**Temperature**: {GEMINI_TEMPERATURE}\n"
                f"**Conversation Memory**: {'Enabled' if ENABLE_CONVERSATION_MEMORY else 'Disabled'}\n"
                f"**Memory Depth**: {MAX_CONVERSATION_HISTORY} messages\n"
                f"**Mood Indicator**: {'Enabled' if ENABLE_MOOD_INDICATOR else 'Disabled'}\n"
                f"**Energy Meter**: {'Enabled' if ENABLE_ENERGY_METER else 'Disabled'}\n"
                f"**User Personalities**: {'Enabled' if USER_SELECTABLE_PERSONALITY else 'Disabled'}"
            ),
            inline=False
        )
        
        # Add auto-response channel info
        if AUTO_RESPONSE_CHANNELS:
            channels_list = []
            for channel_id in AUTO_RESPONSE_CHANNELS:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    channels_list.append(f"<#{channel_id}> (#{channel.name})")
                else:
                    channels_list.append(f"<#{channel_id}>")
            
            embed.add_field(
                name="Auto-Response Channels",
                value="\n".join(channels_list) if channels_list else "None",
                inline=False
            )
        else:
            embed.add_field(
                name="Auto-Response Channels",
                value="None configured",
                inline=False
            )
        
        # Add admin info
        owners = []
        for owner_id in BOT_OWNERS:
            owner = self.bot.get_user(owner_id)
            if owner:
                owners.append(f"{owner.name} ({owner.id})")
            else:
                owners.append(f"User {owner_id}")
        
        embed.add_field(
            name="Administration",
            value=(
                f"**Bot Owners**: {', '.join(owners) if owners else 'None configured'}\n"
                f"**Admin Role**: {ADMIN_ROLE_NAME}"
            ),
            inline=False
        )
        
        # Add footer
        embed.set_footer(text="Powered by Gemini 1.5 AI")
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def preview(self, ctx, target_type: str = None, target_id: Optional[int] = None):
        """
        Show conversation preview for a user or channel.
        
        Usage:
        !preview user @user - Show a specific user's conversation preview
        !preview channel #channel - Show a specific channel's conversation preview
        !preview channel - Show the current channel's conversation preview
        
        Requires the Bot Admin role or being a bot owner.
        """
        if not target_type:
            await ctx.send("Please specify what type of preview to show ('user' or 'channel').")
            return
        
        target_type = target_type.lower()
        
        if target_type not in ["user", "channel"]:
            await ctx.send("Invalid target type. Please use 'user' or 'channel'.")
            return
        
        # Handle user preview
        if target_type == "user":
            # If a user is mentioned, use that user's ID
            if ctx.message.mentions:
                user = ctx.message.mentions[0]
                user_id = user.id
                user_name = user.display_name
            # If a user ID is provided, use that
            elif target_id:
                user = self.bot.get_user(target_id)
                user_id = target_id
                user_name = user.display_name if user else f"User {target_id}"
            else:
                await ctx.send("Please mention a user or provide a user ID.")
                return
            
            # Get the user's conversation preview
            preview = await self.ai_service.get_conversation_preview(user_id=user_id)
            
            if preview:
                embed = discord.Embed(
                    title=f"Conversation Preview for {user_name}",
                    description=preview,
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No conversation history found for {user_name}.")
        
        # Handle channel preview
        elif target_type == "channel":
            # If a channel is mentioned, use that channel's ID
            if ctx.message.channel_mentions:
                channel = ctx.message.channel_mentions[0]
                channel_id = channel.id
                channel_name = channel.name
            # If a channel ID is provided, use that
            elif target_id:
                channel = self.bot.get_channel(target_id)
                channel_id = target_id
                channel_name = channel.name if channel else f"Channel {target_id}"
            # Otherwise, use the current channel
            else:
                channel = ctx.channel
                channel_id = channel.id
                channel_name = channel.name
            
            # Get the channel's conversation preview
            preview = await self.ai_service.get_conversation_preview(channel_id=channel_id)
            
            if preview:
                embed = discord.Embed(
                    title=f"Conversation Preview for #{channel_name}",
                    description=preview,
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No conversation history found for #{channel_name}.")

class GeminiBot(commands.Bot):
    """Discord bot powered by Gemini AI."""
    
    def __init__(self):
        """Initialize the bot with required intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            # Using custom Polish help command set by the cog
            description="A Discord bot powered by Gemini 1.5 AI"
        )
        
        logger.info("Initializing Gemini Discord bot")
    
    async def setup_hook(self):
        """Set up the bot's cogs and extensions."""
        # Add the command cogs
        await self.add_cog(AICommands(self))
        await self.add_cog(AdminCommands(self))
        
        # Create and add the Polish help cog
        from cogs.polish_help import PolishHelpCog
        await self.add_cog(PolishHelpCog(self))
        logger.info("Polish help command cog loaded")
        
        logger.info("Bot setup complete")
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Discord.py version: {discord.__version__}")
        
        # Set bot status
        status_text = BOT_STATUS
        await self.change_presence(activity=discord.Game(name=status_text))
        
        # Log server connections
        guild_list = [f"{guild.name} (ID: {guild.id})" for guild in self.guilds]
        logger.info(f"Connected to {len(self.guilds)} servers: {', '.join(guild_list)}")
        
        print(f"Logged in as {self.user.name}")
        print("The bot is now ready to use!")
        print("-------------------")
    
    async def on_message(self, message):
        """Handle incoming messages."""
        # Ignore messages from self
        if message.author == self.user:
            return
        
        # Process commands first - this handles messages starting with the prefix
        await self.process_commands(message)
        
        # Don't respond to messages that already start with a command prefix
        if message.content.startswith(tuple(AUTO_RESPONSE_IGNORE_PREFIX)):
            return
            
        # Auto-respond if the message is in an auto-response channel
        if message.channel.id in AUTO_RESPONSE_CHANNELS:
            # Let the AI commands cog handle it - it has specific rate limiting
            ai_cog = self.get_cog("AI Commands")
            if ai_cog:
                await ai_cog.on_message(message)
            return
            
        # Auto-respond if it's a direct message (DM)
        if isinstance(message.channel, discord.DMChannel) and ENABLE_DIRECT_MESSAGE_RESPONSES:
            # Let the AI commands cog handle it
            ai_cog = self.get_cog("AI Commands")
            if ai_cog:
                await ai_cog.on_message(message)
            return
            
        # Auto-respond if the bot is mentioned directly
        if ENABLE_MENTION_RESPONSES and self.user in message.mentions:
            # Remove the mention from the message content
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            # If there's actual content after removing the mention
            if content:
                # Create a modified message with the content without the mention
                # (We can't modify the original message, so we'll pass this content to generate_response)
                ai_cog = self.get_cog("AI Commands")
                if ai_cog:
                    # Apply typing indicator
                    async with message.channel.typing():
                        try:
                            # Generate the AI response with conversation memory
                            author_id = message.author.id if ENABLE_CONVERSATION_MEMORY else None
                            channel_id = message.channel.id if ENABLE_CONVERSATION_MEMORY else None
                            author_name = message.author.display_name
                            
                            # Generate the AI response
                            response, conversation = await ai_cog.ai_service.generate_response(
                                content,
                                user_id=author_id, 
                                channel_id=channel_id,
                                author_name=author_name
                            )
                            
                            # Send the response
                            await message.reply(response[:2000])
                            
                            # If response is too long, send the rest as additional messages
                            if len(response) > 2000:
                                chunks = [response[2000:][i:i+1990] for i in range(0, len(response[2000:]), 1990)]
                                for chunk in chunks:
                                    await message.channel.send(chunk)
                        except Exception as e:
                            logger.error(f"Error generating response to mention: {e}")
                            await message.reply("I had trouble generating a response. Try again later.")
            else:
                # If they just mentioned the bot without saying anything else
                await message.reply("Hello! How can I help you today?")
        
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command not found. Try `{BOT_PREFIX}help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}. Try `{BOT_PREFIX}help {ctx.command}` for usage.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.1f}s.")
        else:
            logger.error(f"Command error in {ctx.command}: {error}")
            await ctx.send(f"An error occurred: {str(error)}")

def main():
    """Main entry point to start the bot."""
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        print("ERROR: DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        return
    
    # Create a flag file to track rate limit retries
    rate_limit_file = "discord_rate_limit.tmp"
    retry_count = 0
    
    # Check if we've hit rate limits recently
    if os.path.exists(rate_limit_file):
        try:
            with open(rate_limit_file, "r") as f:
                content = f.read().strip()
                retry_count = int(content) if content.isdigit() else 0
        except:
            retry_count = 0
    
    # If we've had multiple rate limit errors, wait longer before trying again
    if retry_count > 0:
        wait_time = min(retry_count * 60, 3600)  # Max wait 1 hour
        logger.warning(f"Rate limit history detected. Waiting {wait_time} seconds before connecting...")
        print(f"Rate limit history detected. Waiting {wait_time} seconds before connecting...")
        time.sleep(wait_time)
    
    try:
        # Initialize and run the bot
        print("Initializing bot...")
        bot = GeminiBot()
        print("Starting bot...")
        bot.run(token, reconnect=True)
        
        # If we get here, the bot ran successfully, so we can remove the rate limit file
        if os.path.exists(rate_limit_file):
            os.remove(rate_limit_file)
            
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit error
            logger.warning(f"Discord rate limit exceeded. Try again later: {e}")
            print(f"Discord rate limit exceeded. Try again later: {e}")
            
            # Update retry count
            retry_count += 1
            with open(rate_limit_file, "w") as f:
                f.write(str(retry_count))
            
            # Calculate exponential backoff wait time
            wait_time = min(retry_count * 60, 3600)  # Max wait 1 hour
            logger.warning(f"Waiting {wait_time} seconds before attempting to reconnect...")
            print(f"Waiting {wait_time} seconds before attempting to reconnect...")
            time.sleep(wait_time)
            
            # Try to reconnect after waiting
            logger.info("Attempting to reconnect...")
            print("Attempting to reconnect...")
            main()  # Recursive call to try again
        else:
            logger.error(f"Discord HTTP error: {e}")
            print(f"Discord HTTP error: {e}")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"Error starting bot: {e}")
        
        # Wait a bit before trying again if there was an error
        time.sleep(5)

if __name__ == "__main__":
    # Write to a PID file to handle process management
    with open("bot.pid", "w") as f:
        f.write(str(os.getpid()))
    
    try:
        main()
    finally:
        # Clean up the PID file on exit
        if os.path.exists("bot.pid"):
            os.remove("bot.pid")