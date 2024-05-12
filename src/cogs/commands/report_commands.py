import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import json
import mysql.connector
from datetime import datetime
import pytz

from ...my_sql import *
from ...i18n import *
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r', encoding='utf-8') as file:
    config = json.load(file)
color_location = config["color_file_path"]
with open(color_location, 'r') as file:
    color = json.load(file)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)

bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]

bot_invite = config["bot_invite"]
bot_support_server =  config["bot_support_server"]
bot_website =  config["bot_website"]

channel_report_log = config["channel_report_log"]
##########################################################################
language = config["language"]
language_file_path = config["language_file_path"]

translator = Translator(language_file_path, language)
##########################################################################    
def get_id_by_url(url):
    index = url.rfind('/')
    if index != -1:
        return url[index + 1:]
    else:
        return url
##########################################################################

class report_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        self.ctx_menu = app_commands.ContextMenu(name='Report message', callback=self.report_message)
        self.client.tree.add_command(self.ctx_menu) 


    @app_commands.checks.cooldown(1, 300, key=lambda i: (i.guild_id, i.user.id))
    async def report_message(self, interaction: discord.Interaction, message: discord.Message):
        if is_user_banned(interaction.user.id):
            ban_reason = get_ban_reason(interaction.user.id)
            embed = discord.Embed(title=translator.translate("command.report_message.ban_embed.title"), description=translator.translate("command.report_message.ban_embed.description"), color=int(color["red_color"], 16), timestamp=embed_timestamp)
            embed.add_field(name=translator.translate("command.report_message.ban_embed.reason.name"), value=f"`{ban_reason}`")
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
            await interaction.response.send_message(embed=embed, view=BanButtons(), ephemeral=True)
            return

        await interaction.response.send_message(content=translator.translate("command.report_message.message.loading"), ephemeral=True)
        uuid = get_uuid_from_message_id(str(message.id))
        if uuid == None:
            await interaction.edit_original_response(content=translator.translate("command.report_message.error.not_in_database"))
            return     
        
        message_description_raw = message.embeds[0].description
        message_description = message_description_raw.replace('\n', '')
        message_author = get_id_by_url(message.embeds[0].author.url)

        message_content = translator.translate("command.report_message.log_embed.description", message_description=message_description, message_author=message_author, message_id=message.id, uuid=uuid, user_id=interaction.user.id)

        embed = discord.Embed(title=translator.translate("command.report_message.log_embed.title"), description=message_content, color=int(color["red_color"], 16))
        
    #    if message.embeds and message.embeds[0].author:
    #        embed.set_author(name=message.embeds[0].author.name, icon_url=message.embeds[0].author.icon_url, url=message.embeds[0].author.url)
        
        if message.embeds and message.embeds[0].footer:
            embed.set_footer(text=message.embeds[0].footer.text, icon_url=message.embeds[0].footer.icon_url)

        buttons = ReportButtons(message.jump_url)
        channel = interaction.client.get_channel(channel_report_log)
        await channel.send(content=f"{message.content}", embed=embed, view=buttons) 
        await interaction.edit_original_response(content=translator.translate("command.report_message.message.succes"))


        


class ReportButtons(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=10)  
        support_server = discord.ui.Button(label='Message URL', style=discord.ButtonStyle.url, url=url)
        self.add_item(support_server)
#        website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=True)
#        self.add_item(website)

class BanButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)  
        support_server = discord.ui.Button(label='Support Server', style=discord.ButtonStyle.url, url=bot_support_server)
        self.add_item(support_server)
        website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=True)
        self.add_item(website)


async def setup(client:commands.Bot) -> None:
    await client.add_cog(report_commands(client))