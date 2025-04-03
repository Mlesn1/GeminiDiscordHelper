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
        embed.add_field(
            name="About",
            value="This bot uses Google's Gemini 1.5 Flash model to generate responses to your questions and prompts.",
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
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="A Discord bot powered by Google's Gemini 1.5 AI"
        )
    
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
        
        # Set activity status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!ask commands"
            )
        )

    async def on_message(self, message):
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
            
        # Process commands
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