"""
Models for the Discord bot database integration
"""
from datetime import datetime
import os
from sqlalchemy import ForeignKey, create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

# Try to import from Flask app context first
try:
    from app import db
    USING_FLASK_APP = True
except (ImportError, RuntimeError):
    USING_FLASK_APP = False
    # Set up standalone SQLAlchemy for non-Flask usage
    Base = declarative_base()
    
    # Create engine and session
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        # Fallback to SQLite for development/testing
        DATABASE_URL = "sqlite:///discord_bot.db"
    
    engine = create_engine(DATABASE_URL)
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Define the base class for models
if USING_FLASK_APP:
    ModelBase = db.Model
else:
    ModelBase = Base

class User(ModelBase):
    """
    Discord user information
    """
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User discord_id={self.discord_id}, username={self.username}>"


class UserSettings(ModelBase):
    """
    User-specific settings for the Discord bot
    """
    __tablename__ = 'user_settings'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    personality: Mapped[str] = mapped_column(default="balanced")
    max_memory_messages: Mapped[int] = mapped_column(default=50)  # Maximum number of messages to remember
    memory_expiry_days: Mapped[int] = mapped_column(default=7)    # Number of days before memory expires
    default_mood: Mapped[str] = mapped_column(default="thoughtful")
    auto_title_conversations: Mapped[bool] = mapped_column(default=True)  # Auto-generate titles for conversations
    dm_conversation_preview: Mapped[bool] = mapped_column(default=True)   # Send conversation preview as DM
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings for user_id={self.user_id}, personality={self.personality}>"


class Channel(ModelBase):
    """
    Discord channel information
    """
    __tablename__ = 'channels'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Channel discord_id={self.discord_id}, name={self.name}>"


class Conversation(ModelBase):
    """
    Conversation model to group messages
    """
    __tablename__ = 'conversations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=True)
    mood: Mapped[str] = mapped_column(default="thoughtful")
    energy_level: Mapped[int] = mapped_column(default=3)
    title: Mapped[str] = mapped_column(nullable=True)  # User-defined conversation title
    tags: Mapped[str] = mapped_column(nullable=True)   # Comma-separated tags for the conversation
    is_archived: Mapped[bool] = mapped_column(default=False)  # Whether this conversation is archived
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    channel = relationship("Channel", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan")
    
    def __repr__(self):
        if self.user_id:
            return f"<Conversation user_id={self.user_id}, messages={len(self.messages)}>"
        return f"<Conversation channel_id={self.channel_id}, messages={len(self.messages)}>"


class Message(ModelBase):
    """
    Individual message in a conversation
    """
    __tablename__ = 'messages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    role: Mapped[str] = mapped_column()  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column()
    author_name: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")
    
    def __repr__(self):
        return f"<Message role={self.role}, conversation_id={self.conversation_id}>"


# Initialize tables for standalone mode
if not USING_FLASK_APP:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Function to get a database session
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()