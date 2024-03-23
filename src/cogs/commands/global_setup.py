import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import json
import mysql.connector
from datetime import datetime
import pytz
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)
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
database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')

database = config["database"]
##########################################################################

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=database_host,
            port=database_port,
            user=database_user,
            passwd=database_passwd,
            database=database_database
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Fehler bei der Verbindung: {err}")
        return None

connection = connect_to_database()

def guild_exists(server_id):
    try:
        cursor = connection.cursor()
        query = f"SELECT * FROM `{database}` WHERE `guild_id` = %s"
        data = (server_id,)
        cursor.execute(query, data)

        result = cursor.fetchone()
        if result:
            return True
        else:
            return False

    except Exception as e:
        return f"{e}"

def add_guild(server_id, channel_id, invite):
    cursor = connection.cursor()
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    insert_query = f"""
    INSERT INTO `{database}` (`guild_id`, `channel_id`, `invite`, `created_at`)
    VALUES (%s, %s, %s, %s)
    """

    data = (server_id, channel_id, invite, current_datetime)
    try:
        cursor.execute(insert_query, data)
        connection.commit()


    except Exception as e:
        print(f"Fehler beim Einfügen der Daten: {e}")


def remove_guild(guild_id):
    cursor = connection.cursor()

    delete_query = f"DELETE FROM {database} WHERE guild_id = %s"

    try:
        cursor.execute(delete_query, (guild_id,))
        connection.commit()


    except Exception as e:
        print(f"Fehler beim Entfernen der Gilde: {e}")
##########################################################################


class global_setup_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="test", description="Test Command")
    async def add_global(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Test", ephemeral=True)



    

    @app_commands.command(name="add-global", description="Let's you add a Global Chat to your server")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="Specify a channel to become a Global Chat")
    async def add_global(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        try:
            if channel is None:
                channel = interaction.channel
            if interaction.guild is None:
                raise ValueError("This command can only be used in a server.")
            
            if guild_exists(interaction.guild_id):
                embed = discord.Embed(description="You already have a GlobalChat on your server.\r\nPlease note that each server can only have one GlobalChat.", color=int(color["red_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                invite_url = str(await channel.create_invite())
            
                add_guild(interaction.guild_id, channel.id, invite_url)               
                embed = discord.Embed(title="**Welcome to the GlobalChat**", description=f"Your server is ready for action! From now on, all messages in this channel will be broadcasted to all other servers!\n\nThe Global Chat channel is <#{channel.id}>.\n\nPlease note that in the GlobalChat, there should always be a slow mode of at least 5 seconds.", color=int(color["light_green_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)


    @app_commands.command(name="remove-global", description="Let's you remove the Global Chat from your server")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def remove_global(self, interaction: discord.Interaction):
        try:
            if interaction.guild is None:
                raise ValueError("This command can only be used in a server.")
            if guild_exists(interaction.guild_id):
                remove_guild(interaction.guild.id)
                embed = discord.Embed(title="**See you!**", description="The GlobalChat has been removed.\nYou can add it back anytime with </add-global:1177656692545179728>.", color=int(color["light_green_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(description="You don't have a GlobalChat on your server yet.\r\nAdd one with </add-global:1177656692545179728> in a fresh channel.", color=int(color["red_color"], 16), timestamp = embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)


async def setup(client:commands.Bot) -> None:
    await client.add_cog(global_setup_commands(client))

