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
##########################################################################
load_dotenv()

TOKEN = os.getenv('TOKEN')

config_location = os.getenv('config_file')
with open(config_location, 'r', encoding='utf-8') as file:
    config = json.load(file)

admin_guild = config["admin_guild"]
bot_status = config["bot_status"]
##########################################################################
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
##########################################################################
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
        await interaction.response.send_message(f"`⌛` Cooldown. Please retry in **{round(error.retry_after, 1)}** seconds.", ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message("`❌` I don't have sufficient permissions. Please make sure that the BOT has the permissions it's granted with when invited. To fix this error, re-invite the bot using the official invite link.", ephemeral=True)
client.tree.on_error = on_tree_error




client.run(TOKEN)