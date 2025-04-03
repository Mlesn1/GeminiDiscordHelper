#!/usr/bin/env python3
"""
Completely standalone Discord bot script.
This script is specifically designed to run only the Discord bot without any Flask components.
It avoids importing Flask entirely to prevent port conflicts.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
import google.generativeai as genai

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discord_bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GeminiAIService:
    """Service for interacting with the Gemini AI API."""
    
    def __init__(self):
        """Initialize the Gemini AI service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables.")
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
            
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Set up the model
        self.model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini AI service with model: {self.model_name}")
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the Gemini AI model."""
        try:
            # Convert to async operation
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"I encountered an error: {str(e)}"


class AICommands(commands.Cog):
    """Commands for interacting with Gemini AI."""
    
    def __init__(self, bot):
        """Initialize the AI commands cog."""
        self.bot = bot
        self.ai_service = GeminiAIService()
    
    @commands.command()
    async def ask(self, ctx, *, prompt: str):
        """Ask Gemini AI a question or provide a prompt."""
        logger.info(f"User {ctx.author} requested AI response for: {prompt}")
        
        # Show typing indicator while generating response
        async with ctx.typing():
            response = await self.ai_service.generate_response(prompt)
        
        # Send the response, splitting if needed to comply with Discord's message limit
        if len(response) <= 2000:
            await ctx.reply(response)
        else:
            # Split the response into chunks of 2000 characters
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await ctx.reply(f"{chunk}\n(1/{len(chunks)})")
                else:
                    await ctx.send(f"{chunk}\n({i+1}/{len(chunks)})")
    
    @commands.command()
    async def about(self, ctx):
        """Show information about the Gemini AI bot."""
        # Import config for auto-response info
        from config import AUTO_RESPONSE_CHANNELS, GEMINI_MODEL, GEMINI_TEMPERATURE
        
        embed = discord.Embed(
            title="Gemini AI Discord Bot",
            description="A Discord bot powered by Google's Gemini 1.5 AI",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Commands",
            value="• `!ask <prompt>` - Ask Gemini AI a question\n• `!about` - Show this information",
            inline=False
        )
        
        # Add field about auto-response channels if configured
        if AUTO_RESPONSE_CHANNELS:
            channels_info = []
            for channel_id in AUTO_RESPONSE_CHANNELS:
                # In a Cog, we access the bot through self.bot
                channel = self.bot.get_channel(channel_id)
                if channel:
                    channels_info.append(f"<#{channel_id}> (#{channel.name})")
                else:
                    channels_info.append(f"<#{channel_id}>")
            
            auto_response_info = (
                f"The bot will automatically respond to all messages in these channels:\n"
                f"{', '.join(channels_info)}"
            )
            embed.add_field(
                name="Auto-Response Channels",
                value=auto_response_info,
                inline=False
            )
        
        # Add model details
        embed.add_field(
            name="Model",
            value=(
                f"**Model**: {GEMINI_MODEL}\n"
                f"**Temperature**: {GEMINI_TEMPERATURE} (Higher = more creative, Lower = more focused)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="About",
            value=(
                "This bot uses Google's Gemini 1.5 Flash model to generate responses to your questions and prompts. "
                "The Gemini 1.5 model is designed for fast, efficient responses while still providing high-quality AI interactions."
            ),
            inline=False
        )
        
        embed.set_footer(text="Created with ❤️ using discord.py and Google's Generative AI")
        
        await ctx.send(embed=embed)


class GeminiBot(commands.Bot):
    """Discord bot powered by Gemini AI."""
    
    def __init__(self):
        """Initialize the bot with required intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Import here to avoid circular imports
        from config import BOT_PREFIX
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="A Discord bot powered by Google's Gemini 1.5 AI"
        )
        
        # Add cooldown tracking for auto-response channels
        self.last_auto_response = {}
    
    async def setup_hook(self):
        """Set up the bot's cogs and extensions."""
        logger.info("Loading cogs...")
        
        # Add the AI commands cog
        await self.add_cog(AICommands(self))
        logger.info("Loaded AI commands cog")
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Discord.py version: {discord.__version__}")
        logger.info(f"Python version: {sys.version.split()[0]}")
        logger.info(f"Running on: {sys.platform} {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({os.name})")
        logger.info("-------------------")
        
        # Import auto-response channels
        from config import AUTO_RESPONSE_CHANNELS, BOT_STATUS
        
        # Set activity status
        status_text = BOT_STATUS
        if AUTO_RESPONSE_CHANNELS:
            # If we have auto-response channels configured, mention it in the status
            if len(AUTO_RESPONSE_CHANNELS) == 1:
                status_text = f"in 1 auto-response channel"
            else:
                status_text = f"in {len(AUTO_RESPONSE_CHANNELS)} auto-response channels"
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=status_text
            )
        )

    async def on_message(self, message):
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
        
        # Import here to avoid circular imports
        from config import (
            AUTO_RESPONSE_CHANNELS, 
            AUTO_RESPONSE_IGNORE_PREFIX,
            AUTO_RESPONSE_COOLDOWN
        )
        import time
            
        # Auto-respond in designated channels
        if message.channel.id in AUTO_RESPONSE_CHANNELS:
            # Skip processing if message starts with an ignored prefix
            if any(message.content.startswith(prefix) for prefix in AUTO_RESPONSE_IGNORE_PREFIX):
                pass
            # Only respond to non-command messages
            elif not message.content.startswith(self.command_prefix):
                channel_id = message.channel.id
                current_time = time.time()
                
                # Check if we're in cooldown for this channel
                if channel_id in self.last_auto_response:
                    time_since_last = current_time - self.last_auto_response[channel_id]
                    if time_since_last < AUTO_RESPONSE_COOLDOWN:
                        # Still in cooldown, skip processing
                        logger.debug(
                            f"Skipping auto-response in channel {message.channel.name} due to cooldown "
                            f"({time_since_last:.1f}s/{AUTO_RESPONSE_COOLDOWN}s)"
                        )
                        await self.process_commands(message)
                        return
                
                logger.info(f"Auto-responding to {message.author} in channel {message.channel.name}: {message.content}")
                
                # Get AI cog to use its service
                ai_cog = self.get_cog("AI Commands")
                if ai_cog:
                    prompt = message.content
                    
                    # Update cooldown timestamp
                    self.last_auto_response[channel_id] = current_time
                    
                    # Show typing indicator
                    async with message.channel.typing():
                        try:
                            response = await ai_cog.ai_service.generate_response(prompt)
                            
                            # Send the response
                            if len(response) <= 2000:
                                await message.reply(response)
                            else:
                                # Split into chunks for longer responses
                                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                                for i, chunk in enumerate(chunks):
                                    if i == 0:
                                        await message.reply(f"{chunk}\n(1/{len(chunks)})")
                                    else:
                                        await message.channel.send(f"{chunk}\n({i+1}/{len(chunks)})")
                        except Exception as e:
                            logger.error(f"Error in auto-response: {e}")
                            await message.channel.send(f"I encountered an error processing your message: {str(e)}")
        
        # Process commands for all messages
        await self.process_commands(message)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Error: Missing required argument. Try `!help {ctx.command.name}` for more information.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Error: Invalid argument. Try `!help {ctx.command.name}` for more information.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"An error occurred: {error}")


def main():
    """Main entry point to start the bot."""
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        return
    
    try:
        # Initialize and run the bot
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()