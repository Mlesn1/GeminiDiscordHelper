"""
Commands cog for handling AI-related commands.
This module contains the interaction with the Gemini AI service.
"""
import logging
import discord
from discord.ext import commands
from config import COMMAND_COOLDOWN, MAX_RESPONSE_LENGTH, RESPONSE_FOOTER
from utils.ai_service import GeminiAIService

logger = logging.getLogger(__name__)

class AICommands(commands.Cog, name="AI Commands"):
    """Commands for interacting with Gemini 1.5 AI."""
    
    def __init__(self, bot):
        """Initialize the cog with bot instance and AI service."""
        self.bot = bot
        self.ai_service = GeminiAIService()
    
    @commands.command(name="ask", aliases=["gemini", "ai"])
    @commands.cooldown(1, COMMAND_COOLDOWN, commands.BucketType.user)
    async def ask(self, ctx, *, prompt: str):
        """
        Ask Gemini AI a question or provide a prompt.
        
        Usage: !ask <your question or prompt>
        
        Example: !ask What is the capital of France?
        """
        logger.info(f"User {ctx.author} asked: {prompt}")
        
        # Send typing indicator while processing
        async with ctx.typing():
            try:
                # Get AI response
                response = await self.ai_service.generate_response(prompt)
                
                # Handle empty responses
                if not response or response.strip() == "":
                    await ctx.send("⚠️ I couldn't generate a response. Please try again with a different prompt.")
                    return
                
                # Truncate response if it's too long for Discord
                if len(response) + len(RESPONSE_FOOTER) > MAX_RESPONSE_LENGTH:
                    truncated_response = response[:MAX_RESPONSE_LENGTH - len(RESPONSE_FOOTER) - 3] + "..."
                    await ctx.send(truncated_response + RESPONSE_FOOTER)
                    logger.info(f"Response was truncated due to length ({len(response)} characters)")
                else:
                    await ctx.send(response + RESPONSE_FOOTER)
                    
                logger.info(f"Successfully responded to {ctx.author}'s prompt")
                
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                await ctx.send(f"❌ An error occurred while processing your request: {str(e)}")
    
    @commands.command(name="about")
    async def about(self, ctx):
        """Show information about the Gemini AI bot."""
        embed = discord.Embed(
            title="Gemini Discord Bot",
            description="A Discord bot powered by Google's Gemini 1.5 AI model.",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Usage", value=f"Type `{ctx.prefix}ask <your question>` to interact with the AI.", inline=False)
        embed.add_field(name="Model", value="Gemini 1.5", inline=True)
        embed.add_field(name="Created By", value="Your Name", inline=True)
        embed.set_footer(text="Powered by Google's Generative AI")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(AICommands(bot))
