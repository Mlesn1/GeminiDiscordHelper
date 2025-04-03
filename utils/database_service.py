"""
Database service for the Discord bot.
Handles database operations for conversation memory.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from contextlib import contextmanager

from app import db
from models import User, UserSettings, Channel, Conversation, Message

logger = logging.getLogger(__name__)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.session.close()


class DatabaseConversationService:
    """Service for storing and retrieving conversation data from the database."""
    
    def __init__(self):
        """Initialize the database conversation service."""
        logger.info("Database conversation service initialized")
        
    def get_or_create_user(self, discord_id: int, username: str) -> User:
        """
        Get or create a user by Discord ID.
        
        Args:
            discord_id: Discord user ID
            username: Discord username
            
        Returns:
            User object
        """
        with session_scope() as session:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if not user:
                user = User(discord_id=discord_id, username=username)
                session.add(user)
                session.flush()  # Flush to get the ID
                
                # Create default settings
                settings = UserSettings(user_id=user.id, personality="balanced")
                session.add(settings)
                
            return user
    
    def get_or_create_channel(self, discord_id: int, name: Optional[str] = None) -> Channel:
        """
        Get or create a channel by Discord ID.
        
        Args:
            discord_id: Discord channel ID
            name: Channel name (optional)
            
        Returns:
            Channel object
        """
        with session_scope() as session:
            channel = session.query(Channel).filter_by(discord_id=discord_id).first()
            if not channel:
                channel = Channel(discord_id=discord_id, name=name)
                session.add(channel)
                session.flush()  # Flush to get the ID
                
            return channel
    
    def get_user_conversation(self, discord_user_id: int, username: str) -> Tuple[Conversation, List[Dict[str, Any]]]:
        """
        Get or create a conversation for a user.
        
        Args:
            discord_user_id: Discord user ID
            username: Discord username
            
        Returns:
            Tuple of (Conversation object, formatted message history)
        """
        with session_scope() as session:
            # Get or create user
            user = self.get_or_create_user(discord_user_id, username)
            
            # Get or create conversation
            conversation = session.query(Conversation).filter_by(user_id=user.id).first()
            if not conversation:
                conversation = Conversation(user_id=user.id, mood="thoughtful", energy_level=3)
                session.add(conversation)
                session.flush()
            
            # Get message history
            messages = session.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
            
            # Format for API
            formatted_messages = [{"role": msg.role, "parts": [{"text": msg.content}]} for msg in messages]
            
            return conversation, formatted_messages
    
    def get_channel_conversation(self, discord_channel_id: int, channel_name: Optional[str] = None) -> Tuple[Conversation, List[Dict[str, Any]]]:
        """
        Get or create a conversation for a channel.
        
        Args:
            discord_channel_id: Discord channel ID
            channel_name: Channel name (optional)
            
        Returns:
            Tuple of (Conversation object, formatted message history)
        """
        with session_scope() as session:
            # Get or create channel
            channel = self.get_or_create_channel(discord_channel_id, channel_name)
            
            # Get or create conversation
            conversation = session.query(Conversation).filter_by(channel_id=channel.id).first()
            if not conversation:
                conversation = Conversation(channel_id=channel.id, mood="thoughtful", energy_level=3)
                session.add(conversation)
                session.flush()
            
            # Get message history
            messages = session.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
            
            # Format for API
            formatted_messages = [{"role": msg.role, "parts": [{"text": msg.content}]} for msg in messages]
            
            return conversation, formatted_messages
    
    def add_user_message(self, discord_user_id: int, content: str, author_name: str = "") -> Conversation:
        """
        Add a user message to their conversation history.
        
        Args:
            discord_user_id: Discord user ID
            content: Message content
            author_name: Name of the user
            
        Returns:
            Updated conversation
        """
        with session_scope() as session:
            # Get or create user and conversation
            user = self.get_or_create_user(discord_user_id, author_name)
            
            # Get or create conversation
            conversation = session.query(Conversation).filter_by(user_id=user.id).first()
            if not conversation:
                conversation = Conversation(user_id=user.id, mood="thoughtful", energy_level=3)
                session.add(conversation)
                session.flush()
            
            # Create message
            message = Message(
                conversation_id=conversation.id,
                user_id=user.id,
                role="user",
                content=content,
                author_name=author_name
            )
            session.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            # Keep only the most recent messages (limit to 50)
            # This is a hard limit to avoid excessive database size
            messages = session.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
            if len(messages) > 50:
                # Delete older messages
                for old_msg in messages[:-50]:
                    session.delete(old_msg)
            
            return conversation
    
    def add_assistant_message(self, discord_user_id: int, content: str) -> Conversation:
        """
        Add an assistant message to a user's conversation history.
        
        Args:
            discord_user_id: Discord user ID
            content: Message content
            
        Returns:
            Updated conversation
        """
        with session_scope() as session:
            # Get user
            user = session.query(User).filter_by(discord_id=discord_user_id).first()
            if not user:
                logger.error(f"User with Discord ID {discord_user_id} not found")
                return None
            
            # Get conversation
            conversation = session.query(Conversation).filter_by(user_id=user.id).first()
            if not conversation:
                logger.error(f"Conversation for user {discord_user_id} not found")
                return None
            
            # Create message
            message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=content,
                author_name="Gemini"
            )
            session.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            return conversation
    
    def add_channel_user_message(self, discord_channel_id: int, discord_user_id: int, 
                                 content: str, author_name: str = "") -> Conversation:
        """
        Add a user message to a channel's conversation history.
        
        Args:
            discord_channel_id: Discord channel ID
            discord_user_id: Discord user ID
            content: Message content
            author_name: Name of the user
            
        Returns:
            Updated conversation
        """
        with session_scope() as session:
            # Get or create channel and user
            channel = self.get_or_create_channel(discord_channel_id)
            user = self.get_or_create_user(discord_user_id, author_name)
            
            # Get or create conversation
            conversation = session.query(Conversation).filter_by(channel_id=channel.id).first()
            if not conversation:
                conversation = Conversation(channel_id=channel.id, mood="thoughtful", energy_level=3)
                session.add(conversation)
                session.flush()
            
            # Create message
            message = Message(
                conversation_id=conversation.id,
                user_id=user.id,
                role="user",
                content=content,
                author_name=author_name
            )
            session.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            # Keep only the most recent messages (limit to 50)
            messages = session.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
            if len(messages) > 50:
                # Delete older messages
                for old_msg in messages[:-50]:
                    session.delete(old_msg)
            
            return conversation
    
    def add_channel_assistant_message(self, discord_channel_id: int, content: str) -> Conversation:
        """
        Add an assistant message to a channel's conversation history.
        
        Args:
            discord_channel_id: Discord channel ID
            content: Message content
            
        Returns:
            Updated conversation
        """
        with session_scope() as session:
            # Get channel
            channel = session.query(Channel).filter_by(discord_id=discord_channel_id).first()
            if not channel:
                logger.error(f"Channel with Discord ID {discord_channel_id} not found")
                return None
            
            # Get conversation
            conversation = session.query(Conversation).filter_by(channel_id=channel.id).first()
            if not conversation:
                logger.error(f"Conversation for channel {discord_channel_id} not found")
                return None
            
            # Create message
            message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=content,
                author_name="Gemini"
            )
            session.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            return conversation
    
    def clear_user_conversation(self, discord_user_id: int) -> bool:
        """
        Clear a user's conversation history.
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            # Get user
            user = session.query(User).filter_by(discord_id=discord_user_id).first()
            if not user:
                return False
            
            # Get conversation
            conversation = session.query(Conversation).filter_by(user_id=user.id).first()
            if not conversation:
                return False
            
            # Delete all messages
            session.query(Message).filter_by(conversation_id=conversation.id).delete()
            
            return True
    
    def clear_channel_conversation(self, discord_channel_id: int) -> bool:
        """
        Clear a channel's conversation history.
        
        Args:
            discord_channel_id: Discord channel ID
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            # Get channel
            channel = session.query(Channel).filter_by(discord_id=discord_channel_id).first()
            if not channel:
                return False
            
            # Get conversation
            conversation = session.query(Conversation).filter_by(channel_id=channel.id).first()
            if not conversation:
                return False
            
            # Delete all messages
            session.query(Message).filter_by(conversation_id=conversation.id).delete()
            
            return True
    
    def set_user_personality(self, discord_user_id: int, personality: str) -> bool:
        """
        Set a user's personality preference.
        
        Args:
            discord_user_id: Discord user ID
            personality: Personality name
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            # Get user
            user = session.query(User).filter_by(discord_id=discord_user_id).first()
            if not user:
                return False
            
            # Get or create settings
            settings = session.query(UserSettings).filter_by(user_id=user.id).first()
            if not settings:
                settings = UserSettings(user_id=user.id, personality=personality)
                session.add(settings)
            else:
                settings.personality = personality
            
            return True
    
    def get_user_personality(self, discord_user_id: int) -> Optional[str]:
        """
        Get a user's personality preference.
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            Personality name or None if not found
        """
        with session_scope() as session:
            # Get user
            user = session.query(User).filter_by(discord_id=discord_user_id).first()
            if not user:
                return None
            
            # Get settings
            settings = session.query(UserSettings).filter_by(user_id=user.id).first()
            if not settings:
                return None
            
            return settings.personality
    
    def get_conversation_preview(self, discord_user_id: int = None, discord_channel_id: int = None, 
                                max_messages: int = 5) -> List[Dict[str, Any]]:
        """
        Get a preview of recent conversation messages.
        
        Args:
            discord_user_id: Discord user ID (optional)
            discord_channel_id: Discord channel ID (optional)
            max_messages: Maximum number of messages to return
            
        Returns:
            List of messages with role, content, author_name
        """
        with session_scope() as session:
            if discord_user_id:
                # Get user conversation
                user = session.query(User).filter_by(discord_id=discord_user_id).first()
                if not user:
                    return []
                
                conversation = session.query(Conversation).filter_by(user_id=user.id).first()
                if not conversation:
                    return []
                
            elif discord_channel_id:
                # Get channel conversation
                channel = session.query(Channel).filter_by(discord_id=discord_channel_id).first()
                if not channel:
                    return []
                
                conversation = session.query(Conversation).filter_by(channel_id=channel.id).first()
                if not conversation:
                    return []
            else:
                return []
            
            # Get the most recent messages
            messages = (session.query(Message)
                       .filter_by(conversation_id=conversation.id)
                       .order_by(Message.created_at.desc())
                       .limit(max_messages)
                       .all())
            
            # Reverse to get chronological order
            messages.reverse()
            
            # Format for display
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "author_name": msg.author_name or ("You" if msg.role == "user" else "Gemini")
                }
                for msg in messages
            ]