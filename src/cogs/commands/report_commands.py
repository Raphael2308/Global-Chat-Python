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
database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')

database = config["database"]
message_database = config["message_database"]
user_data_databse = config["user_data_databse"]
ban_database = config["ban_database"]
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
##########################################################################
def is_user_banned(user_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = f"SELECT COUNT(*) as count FROM {ban_database} WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()

        connection.commit()
        cursor.close()

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

        connection.commit()
        cursor.close()

        if result:
            ban_reason = result[0]
            return ban_reason
        else:
            return False

    except Exception as e:
        print("Fehler bei der Abfrage: {}".format(str(e)))

def get_uuid_from_message_id(message_id):
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT uuid FROM {message_database} WHERE message_id = %s"
        cursor.execute(query, (message_id,))


        result = cursor.fetchone()

        connection.commit()
        cursor.close()
        
        if result:
            return result['uuid']
        else:
            return None

    except mysql.connector.Error as err:
        print(f"Fehler beim Abrufen der UUID: {err}")
        return None
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
            embed = discord.Embed(title="You are banned", description=f"You have been banned from the Global Chat. If you believe you were banned in error, join the support server and open a ticket.", color=int(color["red_color"], 16), timestamp=embed_timestamp)
            embed.add_field(name="Ban reason", value=f"`{ban_reason}`")
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
            await interaction.response.send_message(embed=embed, view=BanButtons(), ephemeral=True)
            return

        await interaction.response.send_message(f"`🔌` Loading...", ephemeral=True)
        uuid = get_uuid_from_message_id(str(message.id))
        if uuid == None:
            await interaction.edit_original_response(content=f"`❌` Error: The message could not be reported because it was not sent in the global chat.")
            return     
        
        message_description_raw = message.embeds[0].description
        message_description = message_description_raw.replace('\n', '')

        embed = discord.Embed(title=f"Message Reported", description=f"**Message Content:**\n\n```\n{message_description}```\nMessage Author: <@{get_id_by_url(message.embeds[0].author.url)}>\nMessage ID: `{message.id}`\nMessage UUID: `{uuid}`\n\nReportet by: <@{interaction.user.id}>" if message.embeds and message.embeds[0].description else "`❌` Error: No description", color=int(color["red_color"], 16))
        
    #    if message.embeds and message.embeds[0].author:
    #        embed.set_author(name=message.embeds[0].author.name, icon_url=message.embeds[0].author.icon_url, url=message.embeds[0].author.url)
        
        if message.embeds and message.embeds[0].footer:
            embed.set_footer(text=message.embeds[0].footer.text, icon_url=message.embeds[0].footer.icon_url)

        buttons = ReportButtons(message.jump_url)
        channel = interaction.client.get_channel(channel_report_log)
        await channel.send(content=f"{message.content}", embed=embed, view=buttons) 
        await interaction.edit_original_response(content="`✅` Message successfully reported")


        


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