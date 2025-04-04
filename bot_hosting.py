
#!/usr/bin/env python3
"""
Optimized standalone Discord bot for hosting.
No Flask components or web dependencies.
"""
import os
import sys
import logging
from pathlib import Path
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

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

class GeminiAIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")
        
    async def generate_response(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"Error: {str(e)}"

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_service = GeminiAIService()
    
    @commands.command()
    async def ask(self, ctx, *, prompt: str):
        async with ctx.typing():
            response = await self.ai_service.generate_response(prompt)
            await self.send_chunked_response(ctx, response)
    
    async def send_chunked_response(self, ctx, response: str):
        if len(response) <= 2000:
            await ctx.reply(response)
        else:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await ctx.reply(f"{chunk}\n(1/{len(chunks)})")
                else:
                    await ctx.send(f"{chunk}\n({i+1}/{len(chunks)})")

class GeminiBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="Gemini AI Discord Bot"
        )
    
    async def setup_hook(self):
        await self.add_cog(AICommands(self))
        logger.info("AI commands loaded")
    
    async def on_ready(self):
        logger.info(f"Bot ready: {self.user.name} ({self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!ask commands"
            )
        )

def main():
    load_dotenv()
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN not found")
        sys.exit(1)
    
    try:
        bot = GeminiBot()
        bot.run(token, reconnect=True)
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
