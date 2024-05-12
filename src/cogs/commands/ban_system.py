import discord
from discord.ext import commands
from discord import app_commands
from discord import Message, Guild, TextChannel, Permissions
from dotenv import load_dotenv
import os
import json
import mysql.connector
from datetime import datetime
import pytz
from typing import Union

from ...my_sql import *
from ...i18n import *
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r', encoding='utf-8') as file:
    config = json.load(file)
##########################################################################
bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]
admin_guild = config["admin_guild"]
channel_admin_log = config["channel_admin_log"]
##########################################################################
language = config["language"]
language_file_path = config["language_file_path"]

translator = Translator(language_file_path, language)
permission_error_message = translator.translate("cogs.admin_commands.permission_error_message")
##########################################################################
color_location = config["color_file_path"]
with open(color_location, 'r') as file:
    color = json.load(file)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)
##########################################################################
class ban_system(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


    @app_commands.command(name="ban-list", description=translator.translate("command.ban_list.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(manage_messages=True)
    async def ban_list(self, interaction: discord.Interaction):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return    
        if permission_level >= 4:
            banned_users = load_banned_users()
            
            if not banned_users:
                await interaction.response.send_message(content=translator.translate("command.ban_list.message.empty_list"), ephemeral=True)
            else:
                output = ""
                for user in banned_users:
                    output += translator.translate("command.ban_list.ban_list", user_id=user['id'], reason=user['reason'])

                embed = discord.Embed(title=translator.translate("command.ban_list.embed.title"), description=translator.translate("command.ban_list.embed.description", output=output), color=int(color["white_color"], 16), timestamp=embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)


    @app_commands.command(name="ban-user", description=translator.translate("command.ban_user.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(userid=translator.translate("command.ban_user.parameter.userid"))
    @app_commands.describe(reason=translator.translate("command.ban_user.parameter.reason"))
    async def ban_user(self, interaction: discord.Interaction, userid: Union[discord.Member, discord.User], reason: str = "None"):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return  
        if permission_level >= 4:
            userid = str(userid.id)
            if is_user_banned(userid):
                await interaction.response.send_message(content=translator.translate("command.ban_user.error.user_already_banned"), ephemeral=True)
            else:
                ban_user_command(userid, reason)
                embed = discord.Embed(title=translator.translate("command.ban_user.embed.title"), description=translator.translate("command.ban_user.embed.description", user_id=interaction.user.id), color=int(color["light_green_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name=translator.translate("command.ban_user.embed.user.name"), value=f"<@{userid}>")
                embed.add_field(name=translator.translate("command.ban_user.embed.reason.name"), value=f"`{reason}`")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                await interaction.response.send_message(embed=embed, ephemeral=True)

                ban_embed = discord.Embed(title=translator.translate("command.ban_user.log_embed.title"), description=translator.translate("command.ban_user.log_embed.description", user_id=interaction.user.id), color=int(color["red_color"], 16), timestamp=embed_timestamp)
                ban_embed.add_field(name=translator.translate("command.ban_user.log_embed.user.name"), value=f"<@{userid}>")
                ban_embed.add_field(name=translator.translate("command.ban_user.log_embed.reason.name"), value=f"`{reason}`")
                ban_embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                channel = interaction.client.get_channel(channel_admin_log)
                await channel.send(embed=ban_embed)
        else:
            await interaction.response.send_message(content=f"{permission_error_message}", ephemeral=True)

    @app_commands.command(name="unban-user", description=translator.translate("command.unban_user.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.describe(userid=translator.translate("command.unban_user.parameter.userid"))
    @app_commands.default_permissions(manage_messages=True)
    async def unban_user(self, interaction: discord.Interaction, userid: Union[discord.Member, discord.User]):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return  
        if permission_level >= 4:
            userid = str(userid.id)
            if is_user_banned(userid):
                embed = discord.Embed(title=translator.translate("command.unban_user.embed.title"), description=translator.translate("command.unban_user.embed.description", user_id=interaction.user.id), color=int(color["light_green_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name=translator.translate("command.unban_user.embed.user.name"), value=f"<@{userid}>")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                await interaction.response.send_message(embed=embed, ephemeral=True)

                unban_embed = discord.Embed(title=translator.translate("command.unban_user.log_embed.title"), description=translator.translate("command.unban_user.log_embed.description", user_id=interaction.user.id), color=int(color["light_green_color"], 16), timestamp=embed_timestamp)
                unban_embed.add_field(name=translator.translate("command.unban_user.log_embed.user.name"), value=f"<@{userid}>")

                ban_reason = get_ban_reason(userid)
                unban_embed.add_field(name=translator.translate("command.unban_user.log_embed.reason.name"), value=f"`{ban_reason}`")
                unban_embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                channel = interaction.client.get_channel(channel_admin_log)
                await channel.send(embed=unban_embed)

                unban_user_command(userid)
            else:
                await interaction.response.send_message(content=translator.translate("command.unban_user.error.user_is_not_banned"), ephemeral=True)
        else:
            await interaction.response.send_message(content=f"{permission_error_message}", ephemeral=True)


async def setup(client:commands.Bot) -> None:
    await client.add_cog(ban_system(client))