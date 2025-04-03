"""
Database service for the Discord bot.
Handles database operations for conversation memory.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from contextlib import contextmanager
from flask import Flask
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

# Configure logger first
logger = logging.getLogger(__name__)

# Check if we're running in the Flask app context
try:
    # First try importing from app to see if we're in Flask context
    from app import db
    from models import USING_FLASK_APP, User, UserSettings, Channel, Conversation, Message
    logger.info("Using Flask application context for database operations")
except (ImportError, RuntimeError):
    # If not using Flask app context, models.py will define USING_FLASK_APP as False
    # This is the case when running in standalone mode (clean_bot.py)
    from models import USING_FLASK_APP, User, UserSettings, Channel, Conversation, Message
    from models import Base, engine, SessionLocal
    logger.info("Using standalone SQLAlchemy for database operations (no Flask app context)")

# Use the SessionLocal from models.py if not using Flask
if not USING_FLASK_APP:
    # Create a scoped session from SessionLocal
    Session = scoped_session(SessionLocal)
    logger.info("Created scoped database session for standalone mode")
else:
    Session = None
    logger.info("Using Flask-SQLAlchemy session")

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    if USING_FLASK_APP:
        try:
            # Use Flask-SQLAlchemy session
            yield db.session
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            db.session.close()
    else:
        # Use standalone SQLAlchemy session
        if Session is None:
            logger.error("Database session is not available")
            raise RuntimeError("Database connection is not available")
            
        session = Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()


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
            
    def update_user_settings(self, discord_user_id: int, **settings) -> bool:
        """
        Update a user's settings with the provided values.
        
        Args:
            discord_user_id: Discord user ID
            **settings: Settings to update (keyword arguments)
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            # Get user
            user = session.query(User).filter_by(discord_id=discord_user_id).first()
            if not user:
                return False
            
            # Get or create settings
            user_settings = session.query(UserSettings).filter_by(user_id=user.id).first()
            if not user_settings:
                # Create with defaults plus provided settings
                kwargs = {k: v for k, v in settings.items() if hasattr(UserSettings, k)}
                user_settings = UserSettings(user_id=user.id, **kwargs)
                session.add(user_settings)
            else:
                # Update existing settings
                for key, value in settings.items():
                    if hasattr(user_settings, key):
                        setattr(user_settings, key, value)
            
            return True
            
    def get_user_settings(self, discord_user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a user's settings.
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            Dictionary of user settings or None if user not found
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
            
            # Convert to dictionary
            return {
                "personality": settings.personality,
                "max_memory_messages": settings.max_memory_messages,
                "memory_expiry_days": settings.memory_expiry_days,
                "default_mood": settings.default_mood,
                "auto_title_conversations": settings.auto_title_conversations,
                "dm_conversation_preview": settings.dm_conversation_preview
            }
    
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
            
    def set_conversation_title(self, discord_user_id: int = None, discord_channel_id: int = None, 
                              title: str = None) -> bool:
        """
        Set a title for a conversation.
        
        Args:
            discord_user_id: Discord user ID (optional)
            discord_channel_id: Discord channel ID (optional)
            title: Conversation title
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            conversation = self._get_conversation(session, discord_user_id, discord_channel_id)
            if not conversation:
                return False
                
            conversation.title = title
            return True
            
    def add_conversation_tags(self, discord_user_id: int = None, discord_channel_id: int = None,
                             tags: List[str] = None) -> bool:
        """
        Add tags to a conversation.
        
        Args:
            discord_user_id: Discord user ID (optional)
            discord_channel_id: Discord channel ID (optional)
            tags: List of tags to add
            
        Returns:
            True if successful, False otherwise
        """
        if not tags:
            return False
            
        with session_scope() as session:
            conversation = self._get_conversation(session, discord_user_id, discord_channel_id)
            if not conversation:
                return False
                
            # Add new tags to existing ones
            existing_tags = set(conversation.tags.split(',')) if conversation.tags else set()
            existing_tags.update(tags)
            # Remove empty strings
            existing_tags.discard('')
            
            conversation.tags = ','.join(existing_tags)
            return True
            
    def remove_conversation_tags(self, discord_user_id: int = None, discord_channel_id: int = None,
                               tags: List[str] = None) -> bool:
        """
        Remove tags from a conversation.
        
        Args:
            discord_user_id: Discord user ID (optional)
            discord_channel_id: Discord channel ID (optional)
            tags: List of tags to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not tags:
            return False
            
        with session_scope() as session:
            conversation = self._get_conversation(session, discord_user_id, discord_channel_id)
            if not conversation or not conversation.tags:
                return False
                
            # Remove specified tags
            existing_tags = set(conversation.tags.split(','))
            for tag in tags:
                existing_tags.discard(tag)
                
            conversation.tags = ','.join(existing_tags) if existing_tags else None
            return True
            
    def archive_conversation(self, discord_user_id: int = None, discord_channel_id: int = None,
                            archive: bool = True) -> bool:
        """
        Archive or unarchive a conversation.
        
        Args:
            discord_user_id: Discord user ID (optional)
            discord_channel_id: Discord channel ID (optional)
            archive: True to archive, False to unarchive
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            conversation = self._get_conversation(session, discord_user_id, discord_channel_id)
            if not conversation:
                return False
                
            conversation.is_archived = archive
            return True
            
    def get_user_conversations(self, discord_user_id: int, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user.
        
        Args:
            discord_user_id: Discord user ID
            include_archived: Whether to include archived conversations
            
        Returns:
            List of conversation summaries
        """
        with session_scope() as session:
            # Get user
            user = session.query(User).filter_by(discord_id=discord_user_id).first()
            if not user:
                return []
                
            # Get conversations
            query = session.query(Conversation).filter_by(user_id=user.id)
            if not include_archived:
                query = query.filter_by(is_archived=False)
                
            conversations = query.order_by(Conversation.updated_at.desc()).all()
            
            # Format for display
            return [
                {
                    "id": conv.id,
                    "title": conv.title or f"Conversation {conv.id}",
                    "tags": conv.tags.split(',') if conv.tags else [],
                    "mood": conv.mood,
                    "energy_level": conv.energy_level,
                    "is_archived": conv.is_archived,
                    "message_count": len(conv.messages),
                    "updated_at": conv.updated_at.isoformat(),
                    "created_at": conv.created_at.isoformat()
                }
                for conv in conversations
            ]
            
    def _get_conversation(self, session, discord_user_id: int = None, discord_channel_id: int = None) -> Optional[Conversation]:
        """
        Helper method to get a conversation by user or channel ID.
        
        Args:
            session: Database session
            discord_user_id: Discord user ID (optional)
            discord_channel_id: Discord channel ID (optional)
            
        Returns:
            Conversation object or None if not found
        """
        if discord_user_id:
            user = session.query(User).filter_by(discord_id=discord_user_id).first()
            if not user:
                return None
                
            return session.query(Conversation).filter_by(user_id=user.id).first()
            
        elif discord_channel_id:
            channel = session.query(Channel).filter_by(discord_id=discord_channel_id).first()
            if not channel:
                return None
                
            return session.query(Conversation).filter_by(channel_id=channel.id).first()
            
        return None