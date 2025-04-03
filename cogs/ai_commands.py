"""
AI commands cog for the Discord bot.
This module contains commands for interacting with the Gemini 1.5 AI.
"""
import time
import discord
import logging
from discord import app_commands
from discord.ext import commands
from typing import Dict, Optional

from config import (
    COMMAND_COOLDOWN, 
    AUTO_RESPONSE_CHANNELS, 
    AUTO_RESPONSE_IGNORE_PREFIX,
    AUTO_RESPONSE_COOLDOWN,
    RESPONSE_FOOTER,
    MAX_RESPONSE_LENGTH,
    ENABLE_CONVERSATION_MEMORY
)
from utils.ai_service import GeminiAIService

logger = logging.getLogger(__name__)

# Channel cooldown tracking
channel_cooldowns: Dict[int, float] = {}


class AICommands(commands.Cog, name="AI Commands"):
    """Commands for interacting with Gemini 1.5 AI."""

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
        """
        # Apply cooldown
        bucket = self.cooldowns.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            await ctx.send(f"Please wait {retry_after:.1f}s before using this command again.")
            return

        # Show typing indicator while generating response
        async with ctx.typing():
            try:
                # Show that the bot is working on the response
                thinking_msg = await ctx.send("🧠 *Thinking...*")

                # Get user information for conversation memory
                user_id = ctx.author.id if ENABLE_CONVERSATION_MEMORY else None
                author_name = ctx.author.display_name

                # Generate the AI response with conversation memory
                response, conversation_preview = await self.ai_service.generate_response(
                    prompt, 
                    user_id=user_id,
                    author_name=author_name
                )

                # Add the footer to the response if it's not too long
                if len(response) + len(RESPONSE_FOOTER) <= MAX_RESPONSE_LENGTH:
                    response += RESPONSE_FOOTER

                # Split the response if it's too long for Discord
                if len(response) > MAX_RESPONSE_LENGTH:
                    chunks = [response[i:i+MAX_RESPONSE_LENGTH] 
                              for i in range(0, len(response), MAX_RESPONSE_LENGTH)]

                    # Delete the "thinking" message
                    await thinking_msg.delete()

                    # Send the first chunk
                    await ctx.send(chunks[0])

                    # Send additional chunks
                    for chunk in chunks[1:]:
                        await ctx.send(chunk)
                else:
                    # Delete the "thinking" message
                    await thinking_msg.delete()

                    # Send the complete response
                    await ctx.send(response)

                # If we have a conversation preview, send it as an embed
                if conversation_preview:
                    # Only send the preview privately (ephemeral) to the command user
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
                        # If DM fails, send it to the channel
                        await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
                await ctx.send(f"Sorry, I encountered an error: {str(e)}")

    @commands.command()
    async def about(self, ctx):
        """Show information about the Gemini AI bot."""
        embed = discord.Embed(
            title="About Gemini 1.5 AI Bot",
            description="This bot is powered by Google's Gemini 1.5 AI model.",
            color=discord.Color.blue()
        )

        # Add information about usage
        embed.add_field(
            name="Usage",
            value=(
                "**Ask a question**: `!ask <your question>`\n"
                "**Get help**: `!help`\n"
                "**About**: `!about`\n"
                "**Memory settings**: `!memory`\n"
                "**Manage conversations**: `!tag`, `!title`, `!clear`, `!archive`\n"
                "**Send message to channel**: `!say <channel_id> <message>`"
            ),
            inline=False
        )

        # Add information about features
        embed.add_field(
            name="Features",
            value=(
                "• Natural language understanding\n"
                "• Multi-language support\n"
                "• Contextual conversation memory with tagging\n"
                "• Auto-response in designated channels\n"
                "• AI with mood indicators and personalities\n"
                "• User-specific conversation settings\n"
                "• Conversation archiving and organization"
            ),
            inline=False
        )

        # Add bot version and creator info
        embed.add_field(
            name="Technical Details",
            value=(
                "**Model**: Gemini 1.5 Flash\n"
                "**Framework**: discord.py\n"
                "**Hosting**: PythonAnywhere"
            ),
            inline=False
        )

        # Add auto-response channel info if any are configured
        if AUTO_RESPONSE_CHANNELS:
            channels_text = "\n".join([f"<#{channel_id}>" for channel_id in AUTO_RESPONSE_CHANNELS])
            embed.add_field(
                name="Auto-Response Channels",
                value=channels_text,
                inline=False
            )

        # Set footer
        embed.set_footer(text="Powered by Gemini 1.5 AI")

        await ctx.send(embed=embed)

    @commands.command()
    async def say(self, ctx, channel_id: int, *, message: str):
        """Send a message to a specific channel without replying or mentioning.
        Usage: !say <channel_id> <message>"""
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(message)
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send("❌ Channel not found.")
        except Exception as e:
            await ctx.send(f"❌ Error sending message: {e}")

    @commands.command()
    async def autochannel(self, ctx, channel_id: int = None):
        """Set up or remove auto-response for a specific channel.
        Usage: !autochannel <channel_id> - Enable auto-response for channel
               !autochannel - Remove auto-response from current channel"""
        try:
            if channel_id is None:
                # Remove current channel from auto-response list
                if ctx.channel.id in AUTO_RESPONSE_CHANNELS:
                    AUTO_RESPONSE_CHANNELS.remove(ctx.channel.id)
                    await ctx.send(f"✅ Disabled auto-response in this channel")
                else:
                    await ctx.send("❌ Auto-response was not enabled in this channel")
            else:
                # Add new channel to auto-response list
                channel = self.bot.get_channel(channel_id)
                if channel:
                    if channel_id not in AUTO_RESPONSE_CHANNELS:
                        AUTO_RESPONSE_CHANNELS.append(channel_id)
                        await ctx.send(f"✅ Enabled auto-response in channel {channel.name}")
                    else:
                        await ctx.send(f"❌ Auto-response already enabled in {channel.name}")
                else:
                    await ctx.send("❌ Channel not found")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(aliases=["docs", "documentation"])
    async def doc(self, ctx, section: str = None):
        """Display bot documentation in English. Use !doc <section> to view specific sections.
        Available sections: features, commands, memory, settings, auto"""
        await self._send_documentation(ctx, section, language="en")

    @commands.command(aliases=["dokument", "dokumentacja"])
    async def dok(self, ctx, section: str = None):
        """Wyświetl dokumentację bota po polsku. Użyj !dok <sekcja> aby zobaczyć konkretne sekcje.
        Dostępne sekcje: features, commands, memory, settings, auto"""
        await self._send_documentation(ctx, section, language="pl")
        
    async def _send_documentation(self, ctx, section: str = None, language: str = "en"):
        """Internal method to handle documentation in different languages"""
        
        if section and section.lower() not in ["features", "commands", "memory", "settings", "auto"]:
            await ctx.send("❌ Invalid section. Available sections: features, commands, memory, settings, auto")
            return

        if language == "pl":
            error_msg = "❌ Nieprawidłowa sekcja. Dostępne sekcje: features, commands, memory, settings, auto"
        else:
            error_msg = "❌ Invalid section. Available sections: features, commands, memory, settings, auto"

        if not section:
            # Main documentation page
            if language == "pl":
                embed = discord.Embed(
                    title="Dokumentacja Bota Gemini 1.5 AI",
                    description="Witaj w dokumentacji bota! Użyj `!dok <sekcja>` aby zobaczyć szczegółowe informacje o konkretnych funkcjach.",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="📚 Dostępne Sekcje",
                    value=(
                        "• `!dok features` - Przegląd funkcji bota\n"
                        "• `!dok commands` - Lista dostępnych komend\n"
                        "• `!dok memory` - System pamięci rozmów\n"
                        "• `!dok settings` - Ustawienia użytkownika\n"
                        "• `!dok auto` - Konfiguracja auto-odpowiedzi"
                    ),
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="Gemini 1.5 AI Bot Documentation",
                    description="Welcome to the bot documentation! Use `!doc <section>` to view detailed information about specific features.",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="📚 Available Sections",
                    value=(
                        "• `!doc features` - Overview of bot features\n"
                        "• `!doc commands` - List of available commands\n"
                        "• `!doc memory` - Conversation memory system\n"
                        "• `!doc settings` - User settings and customization\n"
                        "• `!doc auto` - Auto-response configuration"
                    ),
                    inline=False
                )
            
        elif section.lower() == "features":
            embed = discord.Embed(
                title="Bot Features",
                description="Key features of the Gemini 1.5 AI Bot",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🤖 Core Features",
                value=(
                    "• Advanced AI responses using Gemini 1.5\n"
                    "• Context-aware conversations\n"
                    "• Multi-language support (English/Polish)\n"
                    "• Customizable personality system\n"
                    "• Auto-response in designated channels"
                ),
                inline=False
            )
            
        elif section.lower() == "commands":
            embed = discord.Embed(
                title="Bot Commands",
                description="List of available commands",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="📝 Basic Commands",
                value=(
                    "• `!ask <question>` - Ask the AI a question\n"
                    "• `!about` - Show bot information\n"
                    "• `!help` or `!pomoc` - Show help menu"
                ),
                inline=False
            )
            embed.add_field(
                name="🧠 Memory Commands",
                value=(
                    "• `!memory` - View memory settings\n"
                    "• `!clear` - Clear conversation history\n"
                    "• `!tag add/remove` - Manage conversation tags"
                ),
                inline=False
            )
            
        elif section.lower() == "memory":
            embed = discord.Embed(
                title="Memory System",
                description="Understanding the conversation memory system",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="💭 Memory Features",
                value=(
                    "• Contextual conversation memory\n"
                    "• Conversation tagging and archiving\n"
                    "• Customizable memory depth\n"
                    "• Memory expiration settings"
                ),
                inline=False
            )
            
        elif section.lower() == "settings":
            embed = discord.Embed(
                title="User Settings",
                description="Customizing your bot experience",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="⚙️ Available Settings",
                value=(
                    "Use `!settings <setting> <value>` to customize:\n"
                    "• `personality`: balanced/professional/creative/friendly/concise\n"
                    "• `default_mood`: thoughtful/cheerful/curious/playful/professional\n"
                    "• `max_memory_messages`: 10-100\n"
                    "• `memory_expiry_days`: 1-30"
                ),
                inline=False
            )
            
        elif section.lower() == "auto":
            embed = discord.Embed(
                title="Auto-Response System",
                description="Understanding automatic responses",
                color=discord.Color.teal()
            )
            embed.add_field(
                name="🔄 Auto-Response Features",
                value=(
                    "• Responds automatically in designated channels\n"
                    "• No need for mentions or commands\n"
                    "• Customizable cooldown periods\n"
                    "• Prefix-based message filtering"
                ),
                inline=False
            )
        
        embed.set_footer(text="For more help, type !help or contact a server administrator")
        await ctx.send(embed=embed)

    @commands.command()
    async def autosend(self, ctx, channel_id: int, interval: int, *, message: str):
        """Send a message periodically to a specified channel.
        Usage: !autosend <channel_id> <interval_seconds> <message>"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await ctx.send("❌ Channel not found.")
                return
                
            while True:
                await channel.send(message)
                await asyncio.sleep(interval)
        except Exception as e:
            await ctx.send(f"❌ Error in auto-send: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-respond to messages in configured channels."""
        # Ignore messages from bots (including self)
        if message.author.bot:
            return

        # Skip if not in an auto-response channel
        if message.channel.id not in AUTO_RESPONSE_CHANNELS:
            return

        # Check if the message starts with an ignored prefix
        for prefix in AUTO_RESPONSE_IGNORE_PREFIX:
            if message.content.startswith(prefix):
                return

        # Apply channel cooldown to prevent spam
        channel_id = message.channel.id
        current_time = time.time()

        if channel_id in channel_cooldowns:
            time_diff = current_time - channel_cooldowns[channel_id]
            if time_diff < AUTO_RESPONSE_COOLDOWN:
                # Still on cooldown, check if we should react to indicate cooldown
                if time_diff < 2:  # Only react if this message came very quickly after the last one
                    try:
                        await message.add_reaction("⏳")  # Hourglass to indicate cooldown
                    except discord.Forbidden:
                        pass  # Can't add reactions
                return

        # Update channel cooldown
        channel_cooldowns[channel_id] = current_time

        # Show that we're processing the message
        async with message.channel.typing():
            try:
                # Get user information for conversation memory
                user_id = message.author.id if ENABLE_CONVERSATION_MEMORY else None
                channel_id = message.channel.id if ENABLE_CONVERSATION_MEMORY else None
                author_name = message.author.display_name

                # Generate the AI response with conversation memory (preferring channel conversation over user)
                response, _ = await self.ai_service.generate_response(
                    message.content,
                    channel_id=channel_id,
                    user_id=user_id,
                    author_name=author_name
                )

                # Add the footer to the response if it's not too long
                if len(response) + len(RESPONSE_FOOTER) <= MAX_RESPONSE_LENGTH:
                    response += RESPONSE_FOOTER

                # Split the response if it's too long for Discord
                if len(response) > MAX_RESPONSE_LENGTH:
                    chunks = [response[i:i+MAX_RESPONSE_LENGTH] 
                              for i in range(0, len(response), MAX_RESPONSE_LENGTH)]

                    # Send all chunks as replies
                    for i, chunk in enumerate(chunks):
                        # First chunk is a reply, rest are regular messages to avoid notification spam
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)
                else:
                    # Send the response as a reply to the original message
                    await message.reply(response)

            except Exception as e:
                logger.error(f"Error generating auto-response: {e}")
                await message.channel.send(f"Sorry, I encountered an error: {str(e)}")


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(AICommands(bot))
    logger.info("AI commands cog loaded")