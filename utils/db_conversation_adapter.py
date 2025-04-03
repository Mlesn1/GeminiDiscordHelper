"""
Adapter to interface between the in-memory ConversationManager and the database-backed conversation storage.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Any, Union
import time
import random

from utils.database_service import DatabaseConversationService
from config import (
    ENABLE_CONVERSATION_MEMORY, MAX_CONVERSATION_HISTORY, CONVERSATION_MEMORY_EXPIRY,
    CONVERSATION_PREVIEW_LENGTH, DEFAULT_MOOD, DEFAULT_PERSONALITY,
    ENABLE_MOOD_INDICATOR, ENABLE_ENERGY_METER
)

logger = logging.getLogger(__name__)

# Check if database should be used
USE_DATABASE = os.environ.get("USE_DATABASE_MEMORY", "true").lower() == "true"

class DBConversationAdapter:
    """
    Adapter that interfaces between the in-memory ConversationManager 
    and the database-backed conversation storage.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        self.db_service = DatabaseConversationService() if USE_DATABASE else None
        logger.info(f"DB Conversation Adapter initialized. Using database: {USE_DATABASE}")

    def get_user_conversation(self, user_id: int, username: str = "") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get or create a user's conversation data from the database.
        
        Args:
            user_id: Discord user ID
            username: Discord username
            
        Returns:
            Tuple of (conversation properties, formatted message history)
        """
        if not USE_DATABASE:
            return {"mood": DEFAULT_MOOD, "personality": DEFAULT_PERSONALITY, "energy_level": 3}, []
        
        try:
            # Get user conversation from database
            conversation, formatted_messages = self.db_service.get_user_conversation(user_id, username)
            
            # Build conversation properties
            props = {
                "mood": conversation.mood or DEFAULT_MOOD,
                "personality": self.db_service.get_user_personality(user_id) or DEFAULT_PERSONALITY,
                "energy_level": conversation.energy_level or 3,
                "conversation_id": conversation.id
            }
            
            return props, formatted_messages
        except Exception as e:
            logger.error(f"Error getting user conversation from database: {e}")
            # Fall back to default values
            return {"mood": DEFAULT_MOOD, "personality": DEFAULT_PERSONALITY, "energy_level": 3}, []
    
    def get_channel_conversation(self, channel_id: int, name: str = "") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get or create a channel's conversation data from the database.
        
        Args:
            channel_id: Discord channel ID
            name: Channel name
            
        Returns:
            Tuple of (conversation properties, formatted message history)
        """
        if not USE_DATABASE:
            return {"mood": DEFAULT_MOOD, "personality": DEFAULT_PERSONALITY, "energy_level": 3}, []
        
        try:
            # Get channel conversation from database
            conversation, formatted_messages = self.db_service.get_channel_conversation(channel_id, name)
            
            # Build conversation properties
            props = {
                "mood": conversation.mood or DEFAULT_MOOD,
                "personality": DEFAULT_PERSONALITY,  # Channels use default personality
                "energy_level": conversation.energy_level or 3,
                "conversation_id": conversation.id
            }
            
            return props, formatted_messages
        except Exception as e:
            logger.error(f"Error getting channel conversation from database: {e}")
            # Fall back to default values
            return {"mood": DEFAULT_MOOD, "personality": DEFAULT_PERSONALITY, "energy_level": 3}, []
    
    def add_user_message(self, user_id: int, content: str, author_name: str = "") -> bool:
        """
        Add a user message to their conversation history.
        
        Args:
            user_id: Discord user ID
            content: Message content
            author_name: Name of the user
            
        Returns:
            True if successful, False otherwise
        """
        if not USE_DATABASE:
            return True
        
        try:
            self.db_service.add_user_message(user_id, content, author_name)
            return True
        except Exception as e:
            logger.error(f"Error adding user message to database: {e}")
            return False
    
    def add_assistant_message(self, user_id: int, content: str) -> bool:
        """
        Add an assistant message to a user's conversation history.
        
        Args:
            user_id: Discord user ID
            content: Message content
            
        Returns:
            True if successful, False otherwise
        """
        if not USE_DATABASE:
            return True
        
        try:
            self.db_service.add_assistant_message(user_id, content)
            return True
        except Exception as e:
            logger.error(f"Error adding assistant message to database: {e}")
            return False
    
    def add_channel_user_message(self, channel_id: int, user_id: int, content: str, author_name: str = "") -> bool:
        """
        Add a user message to a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            user_id: Discord user ID
            content: Message content
            author_name: Name of the user
            
        Returns:
            True if successful, False otherwise
        """
        if not USE_DATABASE:
            return True
        
        try:
            self.db_service.add_channel_user_message(channel_id, user_id, content, author_name)
            return True
        except Exception as e:
            logger.error(f"Error adding channel user message to database: {e}")
            return False
    
    def add_channel_assistant_message(self, channel_id: int, content: str) -> bool:
        """
        Add an assistant message to a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            content: Message content
            
        Returns:
            True if successful, False otherwise
        """
        if not USE_DATABASE:
            return True
        
        try:
            self.db_service.add_channel_assistant_message(channel_id, content)
            return True
        except Exception as e:
            logger.error(f"Error adding channel assistant message to database: {e}")
            return False
    
    def clear_user_conversation(self, user_id: int) -> bool:
        """
        Clear a user's conversation history.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if successful, False otherwise
        """
        if not USE_DATABASE:
            return True
        
        try:
            return self.db_service.clear_user_conversation(user_id)
        except Exception as e:
            logger.error(f"Error clearing user conversation from database: {e}")
            return False
    
    def clear_channel_conversation(self, channel_id: int) -> bool:
        """
        Clear a channel's conversation history.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            True if successful, False otherwise
        """
        if not USE_DATABASE:
            return True
        
        try:
            return self.db_service.clear_channel_conversation(channel_id)
        except Exception as e:
            logger.error(f"Error clearing channel conversation from database: {e}")
            return False
    
    def set_user_personality(self, user_id: int, personality: str) -> bool:
        """
        Set a user's personality preference.
        
        Args:
            user_id: Discord user ID
            personality: Personality name
            
        Returns:
            True if successful, False otherwise
        """
        if not USE_DATABASE:
            return True
        
        try:
            return self.db_service.set_user_personality(user_id, personality)
        except Exception as e:
            logger.error(f"Error setting user personality in database: {e}")
            return False
    
    def get_user_personality(self, user_id: int) -> str:
        """
        Get a user's personality preference.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Personality name (default if not found)
        """
        if not USE_DATABASE:
            return DEFAULT_PERSONALITY
        
        try:
            personality = self.db_service.get_user_personality(user_id)
            return personality or DEFAULT_PERSONALITY
        except Exception as e:
            logger.error(f"Error getting user personality from database: {e}")
            return DEFAULT_PERSONALITY
    
    def get_conversation_preview(self, user_id: Optional[int] = None, 
                                channel_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get a preview of recent conversation messages.
        
        Args:
            user_id: Discord user ID (optional)
            channel_id: Discord channel ID (optional)
            
        Returns:
            List of messages with role, content, author_name
        """
        if not USE_DATABASE:
            return []
        
        try:
            return self.db_service.get_conversation_preview(user_id, channel_id, CONVERSATION_PREVIEW_LENGTH)
        except Exception as e:
            logger.error(f"Error getting conversation preview from database: {e}")
            return []