"""
Models for the Discord bot database integration
"""
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app import db


class User(db.Model):
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


class UserSettings(db.Model):
    """
    User-specific settings for the Discord bot
    """
    __tablename__ = 'user_settings'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    personality: Mapped[str] = mapped_column(default="balanced")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings for user_id={self.user_id}, personality={self.personality}>"


class Channel(db.Model):
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


class Conversation(db.Model):
    """
    Conversation model to group messages
    """
    __tablename__ = 'conversations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=True)
    mood: Mapped[str] = mapped_column(default="thoughtful")
    energy_level: Mapped[int] = mapped_column(default=3)
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


class Message(db.Model):
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