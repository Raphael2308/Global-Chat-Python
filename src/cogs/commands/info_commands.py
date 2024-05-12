import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import json
import mysql.connector
from datetime import datetime
import pytz

from ...i18n import *
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r', encoding='utf-8') as file:
    config = json.load(file)
bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]
bot_invite = config["bot_invite"]
bot_support_server = config["bot_support_server"]
bot_website = config["bot_website"]
bot_website_enabled = config["bot_website_enabled"]
##########################################################################
language = config["language"]
language_file_path = config["language_file_path"]

translator = Translator(language_file_path, language)
##########################################################################
color_location = config["color_file_path"]
with open(color_location, 'r') as file:
    color = json.load(file)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)
##########################################################################


class info_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="help", description=translator.translate("command.help.description"))
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title=translator.translate("command.help.embed.title"), description=translator.translate("command.help.embed.description"), color=int(color["white_color"], 16), timestamp=embed_timestamp)
        embed.add_field(name=translator.translate("command.help.embed.add_global.name"), value=translator.translate("command.help.embed.add_global.value"))
        embed.add_field(name=translator.translate("command.help.embed.remove_global.name"), value=translator.translate("command.help.embed.remove_global.value"))
        embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

        await interaction.response.send_message(embed=embed, ephemeral=True, view=HelpButtons())


class HelpButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)  # times out after 30 seconds
        invite_bot = discord.ui.Button(label='Invite Bot', style=discord.ButtonStyle.url, url=bot_invite)
        self.add_item(invite_bot)
        support_server = discord.ui.Button(label='Support Server', style=discord.ButtonStyle.url, url=bot_support_server)
        self.add_item(support_server)
        if bot_website_enabled == "True":
            website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=False)
        else:
            website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=True)
        self.add_item(website)

async def setup(client:commands.Bot) -> None:
    await client.add_cog(info_commands(client))