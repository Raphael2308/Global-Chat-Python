import json
from colorama import Back, Fore, Style
import time
import platform

import discord
from discord.ext import commands
from discord.ext.commands import CommandOnCooldown
from discord import app_commands
import os
from dotenv import load_dotenv

from src.my_sql import start_connection_checker
import src.i18n as i18n
##########################################################################
load_dotenv()

TOKEN = os.getenv('TOKEN')

config_location = os.getenv('config_file')
with open(config_location, 'r', encoding='utf-8') as file:
    config = json.load(file)

admin_guild = config["admin_guild"]
bot_status = config["bot_status"]
language = config["language"]
language_file_path = config["language_file_path"]

translator = i18n.Translator(language_file_path, language)
##########################################################################
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
##########################################################################
start_connection_checker()
class Client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.cogslist = ["src.cogs.commands.global_setup", "src.cogs.commands.ban_system", "src.cogs.commands.info_commands", "src.cogs.commands.admin_commands","src.cogs.commands.report_commands","src.cogs.global_chat"]

    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(ext)

    async def on_ready(self):
        clear_console()
        prfx = (Back.BLACK + Fore.CYAN + time.strftime("%H:%M:%S", time.gmtime()) + Back.RESET + Fore.WHITE + Style.NORMAL)
        print(prfx + " Logged in as " + Fore.BLUE + self.user.name)
        print(prfx + " Bot ID " + Fore.BLUE + str(self.user.id))
        print(prfx + " Discord Version " + Fore.BLUE+ discord.__version__)
        print(prfx + " Python Version " + Fore.BLUE + str(platform.python_version()))
        guild_only = await self.tree.sync(guild=discord.Object(id=admin_guild))
        print(prfx + " Guild-Only Slash CMDs Synced " + Fore.BLUE + str(len(guild_only)) + " Commands")
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + Fore.BLUE + str(len(synced)) + " Commands")
        print("")
        await client.change_presence(activity = discord.CustomActivity(name=bot_status))

client = Client()
client.remove_command('help')

async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(content=translator.translate("client.tree.cooldown", seconds=round(error.retry_after, 1)), ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message(content=translator.translate("client.tree.bot_missing_Permissions"), ephemeral=True)
client.tree.on_error = on_tree_error




client.run(TOKEN)