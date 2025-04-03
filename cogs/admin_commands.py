"""
Admin commands cog for the Discord bot.
This module contains administrative commands for managing the bot.
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

from config import BOT_OWNERS, ADMIN_ROLE_NAME
from utils.ai_service import GeminiAIService
import utils.db_conversation_adapter

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog, name="Admin Commands"):
    """Administrative commands for managing the bot."""
    
    def __init__(self, bot):
        """Initialize the admin commands cog."""
        self.bot = bot
        self.ai_service = GeminiAIService()
        self.db_adapter = utils.db_conversation_adapter.DBConversationAdapter()
    
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
        from config import (
            GEMINI_MODEL, 
            GEMINI_TEMPERATURE,
            MAX_CONVERSATION_HISTORY,
            ENABLE_CONVERSATION_MEMORY,
            ENABLE_MOOD_INDICATOR
        )
        
        embed.add_field(
            name="Configuration",
            value=(
                f"**Model**: {GEMINI_MODEL}\n"
                f"**Temperature**: {GEMINI_TEMPERATURE}\n"
                f"**Conversation Memory**: {'Enabled' if ENABLE_CONVERSATION_MEMORY else 'Disabled'}\n"
                f"**Memory Depth**: {MAX_CONVERSATION_HISTORY} messages\n"
                f"**Mood Indicator**: {'Enabled' if ENABLE_MOOD_INDICATOR else 'Disabled'}\n"
                f"**User Settings**: Extended user configuration\n"
                f"**Conversation Tagging**: Enabled"
            ),
            inline=False
        )
        
        # Add auto-response channel info
        from config import AUTO_RESPONSE_CHANNELS
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


    @commands.command()
    async def list_user_settings(self, ctx, user_id: Optional[int] = None):
        """
        List all settings for a user.
        
        Usage:
        !list_user_settings @user - List settings for a mentioned user
        !list_user_settings user_id - List settings for a user by ID
        
        Requires the Bot Admin role or being a bot owner.
        """
        # If a user is mentioned, use that user's ID
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            user_id = user.id
            user_name = user.display_name
        # If a user ID is provided, use that
        elif user_id:
            user = self.bot.get_user(user_id)
            user_id = user_id
            user_name = user.display_name if user else f"User {user_id}"
        else:
            await ctx.send("Please mention a user or provide a user ID.")
            return
        
        # Get the user's settings
        settings = self.db_adapter.get_user_settings(user_id)
        
        if settings:
            embed = discord.Embed(
                title=f"User Settings for {user_name}",
                color=discord.Color.blue()
            )
            
            # Add each setting to the embed
            for key, value in settings.items():
                embed.add_field(
                    name=key.replace('_', ' ').title(),
                    value=str(value),
                    inline=True
                )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No settings found for {user_name}.")
    
    @commands.command()
    async def list_user_conversations(self, ctx, user_id: Optional[int] = None, include_archived: bool = False):
        """
        List all conversations for a user.
        
        Usage:
        !list_user_conversations @user - List active conversations for a mentioned user
        !list_user_conversations @user true - Include archived conversations
        !list_user_conversations user_id - List conversations for a user by ID
        
        Requires the Bot Admin role or being a bot owner.
        """
        # If a user is mentioned, use that user's ID
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            user_id = user.id
            user_name = user.display_name
        # If a user ID is provided, use that
        elif user_id:
            user = self.bot.get_user(user_id)
            user_id = user_id
            user_name = user.display_name if user else f"User {user_id}"
        else:
            await ctx.send("Please mention a user or provide a user ID.")
            return
        
        # Get the user's conversations
        conversations = self.db_adapter.get_user_conversations(user_id, include_archived)
        
        if conversations:
            embed = discord.Embed(
                title=f"Conversations for {user_name}",
                description=f"{'All conversations' if include_archived else 'Active conversations only'} ({len(conversations)} found)",
                color=discord.Color.blue()
            )
            
            # Add each conversation to the embed
            for i, convo in enumerate(conversations[:25]):  # Limit to 25 for Discord embed
                title = convo.get('title') or f"Conversation {i+1}"
                status = "🔒 Archived" if convo.get('archived') else "🔓 Active"
                tags = convo.get('tags') or []
                tags_str = ", ".join(tags) if tags else "No tags"
                message_count = convo.get('message_count') or 0
                last_updated = convo.get('last_updated') or "Unknown"
                
                embed.add_field(
                    name=f"{title} ({status})",
                    value=f"Tags: {tags_str}\nMessages: {message_count}\nLast updated: {last_updated}",
                    inline=False
                )
            
            if len(conversations) > 25:
                embed.set_footer(text=f"Showing 25 of {len(conversations)} conversations")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No conversations found for {user_name}.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(AdminCommands(bot))
    logger.info("Admin commands cog loaded")