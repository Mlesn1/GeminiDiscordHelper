#!/usr/bin/env python3
"""
Completely standalone Discord bot with no web components.
This file avoids importing Flask or any web-related modules to prevent port conflicts.
"""
import os
import sys
import logging
import asyncio

# First, mock Flask completely
from types import ModuleType

class DisabledFlask:
    def __init__(self, *args, **kwargs):
        pass
    
    def route(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator
    
    def run(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class DisabledSQLAlchemy:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Mock all Flask-related modules
sys.modules['flask'] = DisabledFlask
sys.modules['flask_sqlalchemy'] = DisabledSQLAlchemy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/discord_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Discord modules
import discord
from discord.ext import commands
import google.generativeai as genai

# Define our AI service
class GeminiAIService:
    """Service for interacting with the Gemini AI API."""
    
    def __init__(self):
        """Initialize the Gemini AI service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.critical("GEMINI_API_KEY not found in environment variables.")
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        self.model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"Initialized Gemini AI service with model: {self.model_name}")
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the Gemini AI model."""
        try:
            response = await asyncio.to_thread(
                lambda: self.model.generate_content(prompt).text
            )
            return response
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"Sorry, I encountered an error: {e}"

class AICommands(commands.Cog, name="AI Commands"):
    """Commands for interacting with Gemini AI."""
    
    def __init__(self, bot):
        """Initialize the AI commands cog."""
        self.bot = bot
        self.ai_service = GeminiAIService()
    
    @commands.command(name="ask")
    async def ask(self, ctx, *, prompt: str):
        """
        Ask Gemini AI a question or provide a prompt.
        
        Usage: !ask <your question or prompt>
        """
        if not prompt or prompt.strip() == "":
            await ctx.send("Please provide a question or prompt. Usage: !ask <your question>")
            return
        
        async with ctx.typing():
            try:
                # Let the user know we're working on it
                await ctx.send(f"Thinking about: '{prompt}'...")
                
                # Generate the AI response
                response = await self.ai_service.generate_response(prompt)
                
                # Send the response
                await ctx.send(response)
            except Exception as e:
                logger.error(f"Error in ask command: {e}")
                await ctx.send(f"Sorry, I encountered an error: {e}")
    
    @commands.command(name="about")
    async def about(self, ctx):
        """Show information about the Gemini AI bot."""
        embed = discord.Embed(
            title="Gemini AI Discord Bot",
            description="A Discord bot powered by Google's Gemini 1.5 AI",
            color=discord.Color.blue()
        )
        embed.add_field(name="Prefix", value="`!`", inline=True)
        embed.add_field(name="Commands", value="`!ask`, `!about`", inline=True)
        embed.add_field(name="Model", value="Gemini 1.5 Flash", inline=True)
        embed.add_field(
            name="Usage", 
            value="Use `!ask <your question>` to ask the AI a question.", 
            inline=False
        )
        embed.set_footer(text="Created with ❤️ using Discord.py and Google Gemini 1.5")
        
        await ctx.send(embed=embed)

class GeminiBot(commands.Bot):
    """Discord bot powered by Gemini AI."""
    
    def __init__(self):
        """Initialize the bot with required intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="A Discord bot powered by Google's Gemini 1.5 AI"
        )
    
    async def setup_hook(self):
        """Set up the bot's cogs and extensions."""
        logger.info("Loading cogs...")
        await self.add_cog(AICommands(self))
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Discord.py version: {discord.__version__}")
        logger.info(f"Python version: {sys.version.split()[0]}")
        logger.info(f"Running on: {sys.platform} {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]} ({os.name})")
        logger.info("-------------------")
    
    async def on_message(self, message):
        """Handle incoming messages."""
        # Don't respond to our own messages
        if message.author == self.user:
            return
        
        # Process commands
        await self.process_commands(message)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command not found. Try `!help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}. Try `!help {ctx.command}` for usage.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"Error: {error}")

def main():
    """Main entry point to start the bot."""
    print("Starting Discord bot in standalone mode")
    logger.info("Starting Discord bot in standalone mode")
    
    # Get Discord token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        return
    
    try:
        # Initialize and run the bot
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit error
            logger.warning(f"Discord rate limit exceeded. Try again later: {e}")
            # Sleep for a bit to allow rate limits to reset
            import time
            time.sleep(60)  # Wait 60 seconds before trying again
        else:
            logger.error(f"Discord HTTP error: {e}")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()