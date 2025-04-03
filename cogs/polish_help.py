"""
Polish language help command cog for the Discord bot.
This module contains a customized help command that displays help information in Polish.
"""
import logging
import discord
from discord.ext import commands
from typing import Mapping, Optional, List, Any

logger = logging.getLogger(__name__)

class PolishHelpCommand(commands.DefaultHelpCommand):
    """A customized help command that displays information in Polish."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.commands_heading = "Komendy"
        self.no_category = "Inne"
        self.command_attrs = {
            "name": "help",
            "help": "Pokazuje tę wiadomość pomocy",
            "aliases": ["pomoc", "komendy"]
        }
    
    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        """Send the bot help page - override to translate to Polish."""
        ctx = self.context
        
        embed = discord.Embed(
            title="Pomoc Gemini 1.5 AI",
            description="Witaj w pomocy bota Gemini AI! Poniżej znajdziesz listę dostępnych komend.",
            color=discord.Color.blue()
        )
        
        # Add general usage information
        embed.add_field(
            name="ℹ️ Jak korzystać z bota",
            value=(
                "• Używaj `!ask <pytanie>` aby zadać pytanie do AI\n"
                "• W wyznaczonych kanałach bot odpowiada automatycznie\n"
                "• Bot zapamiętuje historię rozmów dla lepszego kontekstu\n"
                "• Możesz zarządzać swoimi ustawieniami za pomocą `!memory`"
            ),
            inline=False
        )
        
        # Iterate through cogs and add their commands
        filtered = await self.filter_commands(self.all_commands.values())
        
        # Group commands by cog
        command_map = {}
        for command in filtered:
            cog_name = command.cog_name or self.no_category
            if cog_name not in command_map:
                command_map[cog_name] = []
            command_map[cog_name].append(command)
        
        # Polish translations for cog names
        cog_name_translations = {
            "AI Commands": "Komendy AI",
            "Memory Commands": "Komendy Pamięci",
            "Admin Commands": "Komendy Administracyjne",
            "Other": "Inne"
        }
        
        # Add each category to the embed
        for cog_name, commands_list in command_map.items():
            # Skip empty categories
            if not commands_list:
                continue
            
            # Get the translated name or use original if not found
            translated_name = cog_name_translations.get(cog_name, cog_name)
            
            # Format the commands in this category
            command_texts = []
            for command in commands_list:
                # Get the command signature (name and params)
                signature = self.get_command_signature(command)
                
                # Get the brief description or the first line of help
                brief = command.brief or command.help.split("\n")[0] if command.help else "Brak opisu"
                
                # Translate standard commands
                if command.name == "ask":
                    brief = "Zadaj pytanie do AI"
                elif command.name == "about":
                    brief = "Informacje o bocie Gemini"
                elif command.name == "memory":
                    brief = "Pokaż ustawienia pamięci rozmowy"
                elif command.name == "clear":
                    brief = "Wyczyść historię swojej rozmowy"
                elif command.name == "settings":
                    brief = "Aktualizuj swoje ustawienia rozmowy"
                elif command.name == "tag":
                    brief = "Zarządzaj tagami w swojej rozmowie"
                elif command.name == "title":
                    brief = "Ustaw tytuł dla swojej rozmowy"
                elif command.name == "archive":
                    brief = "Zarchiwizuj swoją obecną rozmowę"
                elif command.name == "listconvo":
                    brief = "Lista twoich rozmów"
                
                command_texts.append(f"`{signature}` - {brief}")
            
            # Add this category to the embed
            embed.add_field(
                name=f"📎 {translated_name}",
                value="\n".join(command_texts),
                inline=False
            )
        
        # Add footer with additional info
        embed.set_footer(text="Użyj !help <komenda> aby uzyskać szczegółową pomoc dla konkretnej komendy.")
        
        await ctx.send(embed=embed)
    
    async def send_command_help(self, command: commands.Command):
        """Send help for a specific command - override to translate to Polish."""
        ctx = self.context
        
        # Create an embed for the command
        embed = discord.Embed(
            title=f"Komenda: {self.get_command_signature(command)}",
            color=discord.Color.blue()
        )
        
        # Command description/help
        help_text = command.help or "Brak szczegółowego opisu."
        
        # Translate standard commands
        if command.name == "ask":
            help_text = (
                "Zadaj pytanie lub podaj prompt do Gemini AI.\n\n"
                "Użycie: !ask <twoje pytanie>\n\n"
                "Przykłady:\n"
                "• !ask Jak działa sztuczna inteligencja?\n"
                "• !ask Napisz krótkie opowiadanie o kosmicznych podróżach\n"
                "• !ask Pomóż mi zrozumieć teorię względności\n\n"
                "Bot zapamiętuje historię rozmowy, więc możesz kontynuować dyskusję."
            )
        elif command.name == "about":
            help_text = "Wyświetla informacje o bocie Gemini AI."
        elif command.name == "memory":
            help_text = (
                "Pokazuje Twoje aktualne ustawienia pamięci rozmowy.\n\n"
                "Użycie: !memory\n\n"
                "Ta komenda wyświetla wszystkie Twoje ustawienia związane z pamięcią rozmowy, "
                "w tym osobowość, nastrój i limity wiadomości."
            )
        elif command.name == "clear":
            help_text = (
                "Wyczyść historię swojej rozmowy z botem.\n\n"
                "Użycie: !clear\n\n"
                "Ta komenda całkowicie usuwa historię Twojej rozmowy i rozpoczyna nową sesję."
            )
        
        embed.description = help_text
        
        # Add aliases if there are any
        if command.aliases:
            aliases = ", ".join(f"`{alias}`" for alias in command.aliases)
            embed.add_field(name="Aliasy", value=aliases, inline=False)
        
        # Add cooldowns if applicable
        if command._buckets and command._buckets._cooldown:
            cooldown = command._buckets._cooldown
            embed.add_field(
                name="Ograniczenie czasowe",
                value=f"{cooldown.rate} użyć na {cooldown.per} sekund",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def send_group_help(self, group: commands.Group):
        """Send help for a command group - override to translate to Polish."""
        ctx = self.context
        
        embed = discord.Embed(
            title=f"Grupa komend: {self.get_command_signature(group)}",
            description=group.help or "Grupa komend bez opisu.",
            color=discord.Color.blue()
        )
        
        # Translate group descriptions for standard groups
        if group.name == "tag":
            embed.description = (
                "Zarządzaj tagami dla swojej aktualnej rozmowy.\n\n"
                "Tagi pomagają organizować i kategoryzować Twoje rozmowy."
            )
        
        # Add subcommands
        filtered = await self.filter_commands(group.commands, sort=True)
        if filtered:
            subcommands = []
            for command in filtered:
                brief = command.brief or command.help.split("\n")[0] if command.help else "Brak opisu"
                
                # Translate standard subcommands
                if group.name == "tag":
                    if command.name == "add":
                        brief = "Dodaj tagi do swojej rozmowy"
                    elif command.name == "remove":
                        brief = "Usuń tagi ze swojej rozmowy"
                
                subcommands.append(f"`{self.get_command_signature(command)}` - {brief}")
            
            if subcommands:
                embed.add_field(
                    name="Podkomendy",
                    value="\n".join(subcommands),
                    inline=False
                )
        
        await ctx.send(embed=embed)


class PolishHelpCog(commands.Cog):
    """Cog that replaces the default help command with a Polish version."""
    
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = PolishHelpCommand()
        bot.help_command.cog = self
        logger.info("Polish help command initialized")
    
    def cog_unload(self):
        """Revert to the original help command when the cog is unloaded."""
        self.bot.help_command = self._original_help_command


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(PolishHelpCog(bot))
    logger.info("Polish help command cog loaded")