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