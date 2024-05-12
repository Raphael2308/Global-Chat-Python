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
##########################################################################
language = config["language"]
language_file_path = config["language_file_path"]

translator = Translator(language_file_path, language)
##########################################################################
bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]
##########################################################################
color_location = config["color_file_path"]
with open(color_location, 'r') as file:
    color = json.load(file)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)
##########################################################################
async def sendAll(self, guild):
    try:
        embed = discord.Embed(title=translator.translate("cogs.global_setup.welcome_embed.title", guild=guild.name), description=translator.translate("cogs.global_setup.welcome_embed.description", guild=guild.name), color=int(color["light_green_color"], 16), timestamp = embed_timestamp)
        embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

        icon = guild.icon
        if icon is not None:
            embed.set_thumbnail(url=icon)

        servers = get_servers()

        for server in servers["servers"]:
            guild: discord.Guild = self.client.get_guild(int(server["guildid"]))
            if guild:
                channel: discord.TextChannel = guild.get_channel(int(server["channelid"]))
                if channel:
                    perms: discord.Permissions = channel.permissions_for(guild.get_member(self.client.user.id))
                    if perms.send_messages:
                        if perms.embed_links and perms.attach_files and perms.external_emojis:
                            sent_message = await channel.send(embed=embed)
    except Exception as e:
        print(f"{e}")
        return f"{e}"
##########################################################################
class global_setup_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
            

    @app_commands.command(name="add-global", description=translator.translate("command.add_global.description"))
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel=translator.translate("command.add_global.parameter.channel"))
    @app_commands.checks.cooldown(1, 100, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_messages=True, moderate_members=True, read_messages=True, use_external_emojis=True, attach_files=True, create_instant_invite=True)
#    @app_commands.checks.bot_has_permissions(send_messages=True)
#    @app_commands.checks.bot_has_permissions(manage_messages=True)
#    @app_commands.check.
    async def add_global(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        try:
            if channel is None:
                channel = interaction.channel
            if interaction.guild is None:
                raise ValueError("This command can only be used in a server.")
            
            if guild_exists(interaction.guild_id):
                embed = discord.Embed(description=translator.translate("command.add_global.error_embed.description"), color=int(color["red_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                invite_url = str(await channel.create_invite())

                add_guild(interaction.guild_id, channel.id, invite_url)
                await channel.edit(slowmode_delay=5)
                embed = discord.Embed(title=translator.translate("command.add_global.embed.title"), description=translator.translate("command.add_global.embed.description", channel=channel.id), color=int(color["light_green_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await sendAll(self, interaction.guild) 

        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(content=translator.translate("command.add_global.message.error"), ephemeral=True)


    @app_commands.command(name="remove-global", description=translator.translate("command.remove_global.description"))
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def remove_global(self, interaction: discord.Interaction):
        try:
            if interaction.guild is None:
                raise ValueError("This command can only be used in a server.")
            if guild_exists(interaction.guild_id):
                remove_guild(interaction.guild.id)
                embed = discord.Embed(title=translator.translate("command.remove_global.embed.title"), description=translator.translate("command.remove_global.embed.description"), color=int(color["light_green_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(description=translator.translate("command.remove_global.error_embed.description"), color=int(color["red_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(content=translator.translate("command.remove_global.message.error"), ephemeral=True)


async def setup(client:commands.Bot) -> None:
    await client.add_cog(global_setup_commands(client))

