"""
Conversation memory management for the Discord bot.
Handles storing, retrieving, and managing conversation history for users and channels.
"""
import time
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from config import (
    MAX_CONVERSATION_HISTORY,
    CONVERSATION_MEMORY_EXPIRY,
    CONVERSATION_PREVIEW_LENGTH,
    MOODS,
    DEFAULT_MOOD,
    MOOD_CHANGE_PROBABILITY,
    ENABLE_MOOD_INDICATOR
)

logger = logging.getLogger(__name__)

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
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history."""
        self.messages.append(message)
        self.last_activity = time.time()
        
        # Keep only the most recent messages up to MAX_CONVERSATION_HISTORY
        if len(self.messages) > MAX_CONVERSATION_HISTORY:
            self.messages = self.messages[-MAX_CONVERSATION_HISTORY:]
    
    def get_formatted_history(self, include_all: bool = False) -> List[Dict[str, str]]:
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
        
        logger.info("Conversation manager initialized")
    
    def get_user_conversation(self, user_id: int) -> Conversation:
        """
        Get or create a conversation for a user.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            The user's conversation
        """
        # Clean up expired conversations periodically
        self._maybe_cleanup()
        
        # Get or create a new conversation for this user
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = Conversation()
        
        return self.user_conversations[user_id]
    
    def get_channel_conversation(self, channel_id: int) -> Conversation:
        """
        Get or create a conversation for a channel.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            The channel's conversation
        """
        # Clean up expired conversations periodically
        self._maybe_cleanup()
        
        # Get or create a new conversation for this channel
        if channel_id not in self.channel_conversations:
            self.channel_conversations[channel_id] = Conversation()
        
        return self.channel_conversations[channel_id]
    
    def add_user_message(self, user_id: int, content: str, author_name: str = "") -> None:
        """
        Add a user message to their conversation history.
        
        Args:
            user_id: Discord user ID
            content: Message content
            author_name: Name of the user
        """
        conversation = self.get_user_conversation(user_id)
        
        message = Message(
            role="user",
            content=content,
            author_name=author_name,
            author_id=user_id
        )
        
        conversation.add_message(message)
    
    def add_assistant_message(self, user_id: int, content: str) -> None:
        """
        Add an assistant's response to a user's conversation history.
        
        Args:
            user_id: Discord user ID
            content: Message content
        """
        conversation = self.get_user_conversation(user_id)
        
        message = Message(
            role="assistant",
            content=content,
            author_name="Gemini",
            author_id=0  # 0 for the bot itself
        )
        
        conversation.add_message(message)
    
    def add_channel_user_message(self, channel_id: int, user_id: int, content: str, author_name: str = "") -> None:
        """
        Add a user message to a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            user_id: Discord user ID
            content: Message content
            author_name: Name of the user
        """
        conversation = self.get_channel_conversation(channel_id)
        
        message = Message(
            role="user",
            content=content,
            author_name=author_name,
            author_id=user_id
        )
        
        conversation.add_message(message)
    
    def add_channel_assistant_message(self, channel_id: int, content: str) -> None:
        """
        Add an assistant's response to a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            content: Message content
        """
        conversation = self.get_channel_conversation(channel_id)
        
        message = Message(
            role="assistant",
            content=content,
            author_name="Gemini",
            author_id=0  # 0 for the bot itself
        )
        
        conversation.add_message(message)
    
    def clear_user_conversation(self, user_id: int) -> bool:
        """
        Clear a user's conversation history.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if the conversation was cleared, False if it didn't exist
        """
        if user_id in self.user_conversations:
            self.user_conversations[user_id] = Conversation()
            return True
        return False
    
    def clear_channel_conversation(self, channel_id: int) -> bool:
        """
        Clear a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            True if the conversation was cleared, False if it didn't exist
        """
        if channel_id in self.channel_conversations:
            self.channel_conversations[channel_id] = Conversation()
            return True
        return False
    
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


# Create a singleton instance
conversation_manager = ConversationManager()