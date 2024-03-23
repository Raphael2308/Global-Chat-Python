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
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)
##########################################################################
permission_error_message = "`❌` You are not staff or your permission level is not high enough."
bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]
admin_guild = config["admin_guild"]
channel_admin_log = config["channel_admin_log"]
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
ban_database = config["ban_database"]
user_data_databse = config["user_data_databse"]
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

def load_banned_users():
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT user_id, reason FROM {ban_database}"
        cursor.execute(query)

        result = cursor.fetchall()
        output_data = [{'id': row['user_id'], 'reason': row['reason']} for row in result]

        return output_data

    except mysql.connector.Error as err:
        print(f"Fehler beim Abrufen der Daten: {err}")

def ban_user_command(user_id, reason):
    try:
        if connection:
            cursor = connection.cursor()
            created_at = datetime.now()

            query = f"INSERT INTO {ban_database} (user_id, reason, created_at) VALUES (%s, %s, %s)"
            data = (user_id, reason, created_at)

            cursor.execute(query, data)
            connection.commit()

    except Exception as e:
        print(f"Fehler beim Hinzufügen des Benutzers: {e}")

def unban_user_command(user_id):
    try:

        if connection:
            cursor = connection.cursor()
            query = f"DELETE FROM {ban_database} WHERE user_id = %s"
            data = (user_id,)

            cursor.execute(query, data)
            connection.commit()
    except Exception as e:
        print(f"Fehler beim Entfernen des Benutzers: {e}")

def is_user_banned(user_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = f"SELECT COUNT(*) as count FROM {ban_database} WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()

        return result['count'] > 0

    except mysql.connector.Error as err:
        print(f"Fehler beim Überprüfen des Nutzers: {err}")
        return False

def get_ban_reason(user_id):
    cursor = connection.cursor()
    try:
        query = f"SELECT reason FROM {ban_database} WHERE user_Id = %s"
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()

        if result:
            ban_reason = result[0]
            return ban_reason
        else:
            return False

    except Exception as e:
        print("Fehler bei der Abfrage: {}".format(str(e)))

def get_user_permission_level(user_id):
    cursor = connection.cursor(dictionary=True)

    try:
        query = f"SELECT permission_level FROM {user_data_databse} WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()
        if result:
            return int(result['permission_level'])
        else:
            return None

    except mysql.connector.Error as err:
        print(f"Fehler beim Abrufen des Permission Levels: {err}")
##########################################################################
class ban_system(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
#    @app_commands.command(name="test", description="Test Command")
#    async def add_global(self, interaction: discord.Interaction):
#        await interaction.response.send_message(f"Test", ephemeral=True)


    @app_commands.command(name="ban-list", description="Outputs the list of banned users")
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
                await interaction.response.send_message(content=f"The ban list is empty.", ephemeral=True)
            else:
                output = "\n".join([f"<@{user['id']}> | Reason: `{user['reason']}`" for user in banned_users])

                embed = discord.Embed(title="Banned Users", description=f"The following users have been banned by admins:\n\n{output}", color=int(color["white_color"], 16), timestamp=embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)


    @app_commands.command(name="ban-user", description="Lets you ban a user from using some Bot features")
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(userid="Enter the User ID of the user")
    @app_commands.describe(reason="Enter the reason why the user should be banned")
    async def ban_user(self, interaction: discord.Interaction, userid: Union[discord.Member, discord.User], reason: str = "None"):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return  
        if permission_level >= 4:
            userid = str(userid.id)
            if is_user_banned(userid):
                await interaction.response.send_message(content="This user is already banned.", ephemeral=True)
            else:
                ban_user_command(userid, reason)
                embed = discord.Embed(title="User Banned", description=f"Your User ID is `{interaction.user.id}`. Thank you for taking action and maintaining a positive environment for the bot. You've successfully banned the following user:", color=int(color["light_green_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name="User", value=f"<@{userid}>")
                embed.add_field(name="Reason", value=f"`{reason}`")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                await interaction.response.send_message(embed=embed, ephemeral=True)

                ban_embed = discord.Embed(title="User Banned", description=f"The Following user was banned by <@{interaction.user.id}>", color=int(color["red_color"], 16), timestamp=embed_timestamp)
                ban_embed.add_field(name="User", value=f"<@{userid}>")
                ban_embed.add_field(name="Reason", value=f"`{reason}`")
                ban_embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                channel = interaction.client.get_channel(channel_admin_log)
                await channel.send(embed=ban_embed)
        else:
            await interaction.response.send_message(content=f"{permission_error_message}", ephemeral=True)

    @app_commands.command(name="unban-user", description="Unbans a user by ID")
    @app_commands.guilds(admin_guild)
    @app_commands.describe(userid="Enter the User ID of the user")
    @app_commands.default_permissions(manage_messages=True)
    async def unban_user(self, interaction: discord.Interaction, userid: Union[discord.Member, discord.User]):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return  
        if permission_level >= 4:
            userid = str(userid.id)
            if is_user_banned(userid):
                embed = discord.Embed(title="User Unbanned", description=f"Your User ID is `{interaction.user.id}`. Thank you for taking action and maintaining a positive environment for the bot. You've successfully unbanned the following user:", color=int(color["light_green_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name="User", value=f"<@{userid}>")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                await interaction.response.send_message(embed=embed, ephemeral=True)

                unban_embed = discord.Embed(title="User Unbanned", description=f"The Following user was unbanned by <@{interaction.user.id}>", color=int(color["light_green_color"], 16), timestamp=embed_timestamp)
                unban_embed.add_field(name="User", value=f"<@{userid}>")

                ban_reason = get_ban_reason(userid)
                unban_embed.add_field(name="Ban Reason", value=f"`{ban_reason}`")
                unban_embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                channel = interaction.client.get_channel(channel_admin_log)
                await channel.send(embed=unban_embed)

                unban_user_command(userid)
            else:
                await interaction.response.send_message(content=f"User is not banned.", ephemeral=True)
        else:
            await interaction.response.send_message(content=f"{permission_error_message}", ephemeral=True)


async def setup(client:commands.Bot) -> None:
    await client.add_cog(ban_system(client))