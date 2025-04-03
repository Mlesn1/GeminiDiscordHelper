#!/usr/bin/env python3
"""
Special workflow entry point that completely bypasses Flask.
This script is designed to be run by the workflow system.
"""
import os
import sys
import logging
from types import ModuleType

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create mock modules to prevent imports
class MockFlaskModule(ModuleType):
    def __init__(self, name):
        super().__init__(name)
        
    def __getattr__(self, name):
        return self._mock_attr
        
    def _mock_attr(self, *args, **kwargs):
        return None

# Install mocks before any other imports
sys.modules['flask'] = MockFlaskModule('flask')
sys.modules['flask_sqlalchemy'] = MockFlaskModule('flask_sqlalchemy')

# Now we can safely import the Discord modules
try:
    import discord
    from discord.ext import commands
    from dotenv import load_dotenv
    import google.generativeai as genai
except ImportError as e:
    logger.critical(f"Failed to import required libraries: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Bot configuration
PREFIX = "!"
GEMINI_MODEL = "gemini-1.5-flash"
ABOUT_TEXT = """
🤖 **Gemini AI Discord Bot**

A Discord bot powered by Google's Gemini 1.5 AI model.
Use commands like `!ask` to interact with the AI.

**Commands:**
• `!ask <prompt>` - Ask a question or provide a prompt
• `!about` - Show information about this bot

Created with ❤️ using Python and Discord.py
"""

class GeminiAIService:
    """Service for interacting with the Gemini AI API."""
    
    def __init__(self):
        """Initialize the Gemini AI service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.critical("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY not set in environment")
            
        genai.configure(api_key=self.api_key)
        self.model = GEMINI_MODEL
        logger.info(f"Initialized Gemini AI service with model: {self.model}")
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the Gemini AI model."""
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

class AICommands(commands.Cog):
    """Commands for interacting with Gemini AI."""
    
    def __init__(self, bot):
        """Initialize the AI commands cog."""
        self.bot = bot
        self.ai_service = GeminiAIService()
    
    @commands.command(name="ask")
    async def ask(self, ctx, *, prompt: str):
        """Ask Gemini AI a question or provide a prompt."""
        async with ctx.typing():
            response = await self.ai_service.generate_response(prompt)
            
            # Split response into chunks if it's too long
            if len(response) > 1900:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(response)
    
    @commands.command(name="about")
    async def about(self, ctx):
        """Show information about the Gemini AI bot."""
        await ctx.send(ABOUT_TEXT)

class GeminiBot(commands.Bot):
    """Discord bot powered by Gemini AI."""
    
    def __init__(self):
        """Initialize the bot with required intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="A Discord bot powered by Google's Gemini 1.5 AI"
        )
        
    async def setup_hook(self):
        """Set up the bot's cogs and extensions."""
        logger.info("Loading cogs...")
        try:
            await self.add_cog(AICommands(self))
            logger.info("Loaded AI commands cog")
        except Exception as e:
            logger.error(f"Error loading AI commands cog: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Discord.py version: {discord.__version__}")
        logger.info(f"Python version: {sys.version.split()[0]}")
        logger.info(f"Running on: {sys.platform}")
        logger.info("-------------------")
        
        # Set bot activity
        activity = discord.Activity(type=discord.ActivityType.listening, name="!ask commands")
        await self.change_presence(activity=activity)

def main():
    """Start the Discord bot."""
    logger.info("Starting Discord bot workflow version...")
    
    # Get Discord token from environment
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found in environment variables")
        print("Error: DISCORD_TOKEN not set. Please set it in .env file or environment variables.")
        return
    
    # Initialize and run bot
    bot = GeminiBot()
    
    try:
        bot.run(token, reconnect=True)
    except discord.errors.LoginFailure:
        logger.critical("Invalid Discord token. Please check your DISCORD_TOKEN.")
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()