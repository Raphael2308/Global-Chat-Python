import json
from colorama import Back, Fore, Style
import time
import platform
import asyncio
from typing import Union
import mysql.connector
import schedule

from typing import Callable, Optional

import discord
from discord.ext import commands
from discord.ext.commands import CommandOnCooldown
from discord import Message, Guild, TextChannel, Permissions
from discord import ui
from discord.app_commands import Parameter
from discord import app_commands
import os
from dotenv import load_dotenv
from colorama import Back, Fore, Style


##########################################################################
load_dotenv()

TOKEN = os.getenv('TOKEN')

config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)

admin_guild = config["admin_guild"]
##########################################################################
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
##########################################################################
class Client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.cogslist = ["cogs.commands.global_setup", "cogs.commands.ban_system"]

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


client = Client()
client.run(TOKEN)