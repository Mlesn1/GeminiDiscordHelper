"""
Bot module defining the core Discord bot class with event handlers and setup.
"""
import logging
import discord
from discord.ext import commands
import os
import platform
from config import BOT_PREFIX, BOT_DESCRIPTION, BOT_STATUS

logger = logging.getLogger(__name__)

class GeminiBot(commands.Bot):
    """Discord bot powered by Gemini 1.5 AI."""
    
    def __init__(self):
        """Initialize the bot with required intents and command prefix."""
        intents = discord.Intents.all()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            description=BOT_DESCRIPTION,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )
    
    async def setup_hook(self):
        """Setup hook called when the bot is being prepared to connect to Discord."""
        # Load all cogs
        logger.info("Loading cogs...")
        
        cogs_to_load = [
            "cogs.ai_commands",
            "cogs.admin_commands",
            "cogs.memory_commands"
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded {cog}")
            except Exception as e:
                logger.error(f"Failed to load {cog}: {e}")
    
    async def on_ready(self):
        """Event handler that is called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Discord.py version: {discord.__version__}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        logger.info("-------------------")
        
        # Set bot status
        activity = discord.Game(name=BOT_STATUS)
        await self.change_presence(status=discord.Status.online, activity=activity)
    
    async def on_message(self, message):
        """Event handler for messages in servers."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
        
        # Log the message for debugging
        logger.info(f"Message from {message.author}: {message.content}")
        
        # Check if the bot was mentioned
        if self.user.mentioned_in(message) and not message.mention_everyone:
            logger.info(f"Bot was mentioned by {message.author} in {message.channel}")
            # Remove the mention from the prompt
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            if content:
                # Get the AI commands cog
                ai_cog = self.get_cog("AI Commands")
                if ai_cog:
                    ctx = await self.get_context(message)
                    await ai_cog.ask(ctx, prompt=content)
                else:
                    logger.error("AI Commands cog not found")
                    await message.channel.send("❌ Error: AI service is not available.")
        
        # Process commands as usual (for prefix commands)
        await self.process_commands(message)
    
    async def on_command_error(self, ctx, error):
        """Global error handler for command errors."""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❓ Command not found. Use `{BOT_PREFIX}help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ Missing required argument: {error.param.name}")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"❌ An error occurred: {error}")
