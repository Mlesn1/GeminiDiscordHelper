"""
Memory management commands cog for the Discord bot.
This module contains commands for users to manage their conversation memory and settings.
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List, Dict, Any

from config import ENABLE_CONVERSATION_MEMORY
from utils.ai_service import GeminiAIService
from utils.db_conversation_adapter import DBConversationAdapter

logger = logging.getLogger(__name__)

class MemoryCommands(commands.Cog, name="Memory Commands"):
    """Commands for managing conversation memory and settings."""
    
    def __init__(self, bot):
        """Initialize the memory commands cog."""
        self.bot = bot
        self.ai_service = GeminiAIService()
        self.db_adapter = DBConversationAdapter()
        
        logger.info("Memory commands cog initialized")
    
    async def cog_check(self, ctx):
        """Check if conversation memory is enabled."""
        if not ENABLE_CONVERSATION_MEMORY:
            await ctx.send("Conversation memory is currently disabled.")
            return False
        return True
    
    @commands.command()
    async def memory(self, ctx):
        """
        Show your current conversation memory settings and status.
        
        Usage: !memory
        """
        # Get the user's settings
        user_id = ctx.author.id
        settings = self.db_adapter.get_user_settings(user_id)
        
        # Create an embed to display the settings
        embed = discord.Embed(
            title="Your Conversation Memory Settings",
            description="These settings control how the bot remembers and manages your conversations.",
            color=discord.Color.blue()
        )
        
        # Add fields for each setting
        embed.add_field(
            name="Memory Status",
            value="✅ Enabled" if ENABLE_CONVERSATION_MEMORY else "❌ Disabled",
            inline=True
        )
        
        embed.add_field(
            name="Default Mood",
            value=settings["default_mood"].capitalize(),
            inline=True
        )
        
        embed.add_field(
            name="Personality",
            value=settings["personality"].capitalize(),
            inline=True
        )
        
        embed.add_field(
            name="Message Limit",
            value=f"{settings['max_memory_messages']} messages",
            inline=True
        )
        
        embed.add_field(
            name="Memory Expiry",
            value=f"{settings['memory_expiry_days']} days",
            inline=True
        )
        
        embed.add_field(
            name="Auto-title Conversations",
            value="✅ Enabled" if settings["auto_title_conversations"] else "❌ Disabled",
            inline=True
        )
        
        embed.add_field(
            name="Send DM Previews",
            value="✅ Enabled" if settings["dm_conversation_preview"] else "❌ Disabled",
            inline=True
        )
        
        # Add commands help - Basic commands
        embed.add_field(
            name="Basic Commands",
            value=(
                "`!memory` - Show these settings\n"
                "`!clear` - Clear your conversation history\n"
                "`!settings <setting> <value>` - Update a specific setting"
            ),
            inline=False
        )
        
        # Add commands help - Organization commands
        embed.add_field(
            name="Conversation Organization",
            value=(
                "`!tag add <tag1> <tag2>...` - Add tags to your conversation\n"
                "`!tag remove <tag1> <tag2>...` - Remove tags from your conversation\n"
                "`!title <title>` - Set a title for your conversation\n"
                "`!archive` - Archive your current conversation\n"
                "`!listconvo` - List your active conversations\n"
                "`!listconvo true` - List all your conversations including archived"
            ),
            inline=False
        )
        
        # Set footer
        embed.set_footer(text="These settings are specific to your account and persist between bot restarts.")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="clear")
    async def clear_memory(self, ctx):
        """
        Clear your conversation history with the bot.
        
        Usage: !clear
        """
        user_id = ctx.author.id
        
        # Clear the user's conversation
        success = await self.ai_service.clear_conversation(user_id=user_id)
        
        if success:
            await ctx.send("✅ Your conversation history has been cleared.")
        else:
            await ctx.send("There was no conversation history to clear.")
    
    @commands.group(name="tag", invoke_without_command=True)
    async def tag(self, ctx):
        """
        Manage tags for your current conversation.
        
        Usage:
        !tag - Show current tags
        !tag add <tag1> <tag2>... - Add tags to your conversation
        !tag remove <tag1> <tag2>... - Remove tags from your conversation
        """
        if ctx.invoked_subcommand is None:
            user_id = ctx.author.id
            
            # Get conversation preview which includes tags
            conversations = self.db_adapter.get_user_conversations(user_id)
            
            if not conversations:
                await ctx.send("You don't have any active conversations.")
                return
            
            # Get the most recent (current) conversation
            current_conversation = conversations[0]
            
            if not current_conversation.get("tags"):
                await ctx.send("Your current conversation doesn't have any tags. Use `!tag add <tag>` to add tags.")
            else:
                tags_str = ", ".join([f"`{tag}`" for tag in current_conversation["tags"]])
                await ctx.send(f"Tags for your current conversation: {tags_str}")
    
    @tag.command(name="add")
    async def tag_add(self, ctx, *tags):
        """
        Add tags to your current conversation.
        
        Usage: !tag add <tag1> <tag2>...
        """
        if not tags:
            await ctx.send("Please specify at least one tag to add.")
            return
        
        user_id = ctx.author.id
        success = self.db_adapter.add_conversation_tags(user_id=user_id, tags=list(tags))
        
        if success:
            tags_str = ", ".join([f"`{tag}`" for tag in tags])
            await ctx.send(f"✅ Added {tags_str} to your conversation tags.")
        else:
            await ctx.send("Failed to add tags. Make sure you have an active conversation.")
    
    @tag.command(name="remove")
    async def tag_remove(self, ctx, *tags):
        """
        Remove tags from your current conversation.
        
        Usage: !tag remove <tag1> <tag2>...
        """
        if not tags:
            await ctx.send("Please specify at least one tag to remove.")
            return
        
        user_id = ctx.author.id
        success = self.db_adapter.remove_conversation_tags(user_id=user_id, tags=list(tags))
        
        if success:
            tags_str = ", ".join([f"`{tag}`" for tag in tags])
            await ctx.send(f"✅ Removed {tags_str} from your conversation tags.")
        else:
            await ctx.send("Failed to remove tags. Make sure you have an active conversation with these tags.")
    
    @commands.command(name="title")
    async def set_title(self, ctx, *, title=None):
        """
        Set a title for your current conversation.
        
        Usage: !title Your Conversation Title
        """
        if not title:
            await ctx.send("Please provide a title for your conversation.")
            return
        
        user_id = ctx.author.id
        success = self.db_adapter.set_conversation_title(user_id=user_id, title=title)
        
        if success:
            await ctx.send(f"✅ Your conversation title has been set to: **{title}**")
        else:
            await ctx.send("Failed to set conversation title. Make sure you have an active conversation.")
    
    @commands.command(name="archive")
    async def archive_conversation(self, ctx):
        """
        Archive your current conversation.
        
        Usage: !archive
        """
        user_id = ctx.author.id
        success = self.db_adapter.archive_conversation(user_id=user_id, archive=True)
        
        if success:
            await ctx.send("✅ Your conversation has been archived. Starting a new conversation.")
            # Clear the conversation to start a new one
            await self.ai_service.clear_conversation(user_id=user_id)
        else:
            await ctx.send("Failed to archive conversation. Make sure you have an active conversation.")
    
    @commands.command(name="listconvo", aliases=["conversations", "listconvos"])
    async def list_conversations(self, ctx, include_archived: bool = False):
        """
        List your conversations.
        
        Usage: 
        !listconvo - List your active conversations
        !listconvo true - List all conversations including archived ones
        """
        user_id = ctx.author.id
        conversations = self.db_adapter.get_user_conversations(user_id, include_archived)
        
        if not conversations:
            await ctx.send("You don't have any conversations yet.")
            return
        
        # Create embed with conversation list
        embed = discord.Embed(
            title="Your Conversations",
            description=f"Found {len(conversations)} conversation(s).",
            color=discord.Color.blue()
        )
        
        # Add each conversation to the embed
        for i, convo in enumerate(conversations[:10]):  # Limit to 10 to avoid embed size limit
            # Format date to readable format
            updated_at = convo["updated_at"].split("T")[0]
            
            # Get tags or placeholder
            tags = ", ".join(convo["tags"]) if convo["tags"] else "No tags"
            
            # Format conversation info
            value = (
                f"**ID**: {convo['id']}\n"
                f"**Updated**: {updated_at}\n"
                f"**Messages**: {convo['message_count']}\n"
                f"**Tags**: {tags}\n"
                f"**Status**: {'Archived' if convo['is_archived'] else 'Active'}"
            )
            
            embed.add_field(
                name=f"{i+1}. {convo['title']}",
                value=value,
                inline=False
            )
        
        # Add note if there are more conversations
        if len(conversations) > 10:
            embed.set_footer(text=f"Showing 10 of {len(conversations)} conversations. Use specific commands to manage them.")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="settings")
    async def update_settings(self, ctx, setting: str = None, value: str = None):
        """
        Update your conversation memory settings.
        
        Usage: !settings <setting> <value>
        
        Available settings:
        - personality: balanced, professional, creative, friendly, concise
        - default_mood: thoughtful, cheerful, curious, playful, professional
        - max_memory_messages: 10-100 (number of messages to remember)
        - memory_expiry_days: 1-30 (days before memory expires)
        - auto_title_conversations: true/false
        - dm_conversation_preview: true/false
        """
        if not setting or not value:
            await ctx.send("Please provide both a setting name and value. Use `!memory` to see available settings.")
            return
        
        user_id = ctx.author.id
        setting = setting.lower()
        
        # Define valid values for each setting
        valid_settings = {
            "personality": ["balanced", "professional", "creative", "friendly", "concise"],
            "default_mood": ["thoughtful", "cheerful", "curious", "playful", "professional"],
            "max_memory_messages": lambda v: v.isdigit() and 10 <= int(v) <= 100,
            "memory_expiry_days": lambda v: v.isdigit() and 1 <= int(v) <= 30,
            "auto_title_conversations": lambda v: v.lower() in ["true", "false", "yes", "no", "1", "0"],
            "dm_conversation_preview": lambda v: v.lower() in ["true", "false", "yes", "no", "1", "0"]
        }
        
        # Check if the setting is valid
        if setting not in valid_settings:
            valid_settings_list = ", ".join(f"`{s}`" for s in valid_settings.keys())
            await ctx.send(f"Invalid setting. Available settings: {valid_settings_list}")
            return
        
        # Validate and convert the value
        validator = valid_settings[setting]
        if callable(validator):
            if not validator(value):
                await ctx.send(f"Invalid value for `{setting}`. Please check the command help for valid values.")
                return
            
            # Convert numeric values
            if setting in ["max_memory_messages", "memory_expiry_days"]:
                value = int(value)
            # Convert boolean values
            elif setting in ["auto_title_conversations", "dm_conversation_preview"]:
                value = value.lower() in ["true", "yes", "1"]
        else:
            # Check against list of valid values
            if value.lower() not in validator:
                valid_values = ", ".join(f"`{v}`" for v in validator)
                await ctx.send(f"Invalid value for `{setting}`. Valid options: {valid_values}")
                return
            value = value.lower()
        
        # Update the setting
        success = self.db_adapter.update_user_settings(user_id, **{setting: value})
        
        if success:
            await ctx.send(f"✅ Your `{setting}` setting has been updated to: **{value}**")
        else:
            await ctx.send(f"Failed to update your settings. Please try again later.")


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(MemoryCommands(bot))
    logger.info("Memory commands cog loaded")