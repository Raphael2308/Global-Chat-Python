import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import json
import mysql.connector
from datetime import datetime
import pytz
import string
import random

import re
from better_profanity import profanity
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)
##########################################################################
bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]
bot_support_server = config["bot_support_server"]
bot_website = config["bot_website"]
standard_server_icon = config["standard_server_icon"]
##########################################################################
swear_word_list = config["swear_file_path"]
emoji_list = config["emoji_file_path"]
color_location = config["color_file_path"]
bot_settings = config["bot_settings_file_path"]
with open(color_location, 'r') as file:
    color = json.load(file)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)

global_chat_cooldown = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)

block_reason = {
    "|": "Banned Unicode character",
    "||": "Swear word blocked",
    "|||": "Link blocked"
}
role_prefix = {
  "developer": "<:developer:1177680732966101133>  DEV",
  "admin": "<:admin:1177681171103096862>  Admin",
  "moderator": "<:moderator:1177682704830050444>  MOD",
  "partner": "<:partner:1179864775761604728>  Partner",
  "vip": "<:vip:1177945496401223751>  VIP",
  "default": ""
}
role_color = {
  "developer": 0x5865f2,
  "admin": 0xf54651,
  "moderator": 0xfc964b,
  "partner": 0x4dbc62,
  "vip": 0xfbb848,
  "default": 0xffffff
}
discord_url = "https://discordapp.com/users/"
##########################################################################
database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')

database = config["database"]
database = config["database"]
ban_database = config["ban_database"]
user_data_databse = config["user_data_databse"]
message_database = config["message_database"]
##########################################################################
def read_settings_variable(variable_name):
    try:
        with open(bot_settings, 'r') as file:
            config_data = json.load(file)
        value = config_data.get(variable_name)


            
        if value is not None:
            if value == "true" or value == "false":
                if value == "true":
                    return True
                else:
                    return False
    
            return value
        else:
            print(f'Die Variable "{variable_name}" wurde nicht gefunden.')
            return None
    
    except FileNotFoundError:
        print('Die Konfigurationsdatei wurde nicht gefunden.')
        return None
    except json.JSONDecodeError:
        print('Fehler beim Dekodieren der JSON-Datei.')
        return None
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

def get_globalchat(guild_id, channel_id=None):
    cursor = connection.cursor(dictionary=True)

    try:
        select_query = f"SELECT channel_id, invite FROM {database} WHERE guild_id = %s"
        cursor.execute(select_query, (guild_id,))
        result = cursor.fetchone()

        if result:
            if str(channel_id) == str(result['channel_id']):
                return {'guildid': guild_id, 'channelid': result['channel_id'], 'invite': result['invite']}
            else:
                return None
        else:
            return None

    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return None

def is_user_in_data(user_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = f"SELECT COUNT(*) as count FROM {user_data_databse} WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()
        return result['count'] > 0

    except mysql.connector.Error as err:
        print(f"Fehler beim Überprüfen des Nutzers: {err}")
        return False
    
def get_user_role(user_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = f"SELECT role FROM {user_data_databse} WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()
        if result:
            return result['role']
        else:
            return "Nutzer nicht gefunden"

    except mysql.connector.Error as err:
        print(f"Fehler beim Abrufen der Rolle: {err}")

def get_uuid_from_message_id(message_id):
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT uuid FROM {message_database} WHERE message_id = %s"
        cursor.execute(query, (message_id,))


        result = cursor.fetchone()
        if result:
            return result['uuid']
        else:
            return None

    except mysql.connector.Error as err:
        print(f"Fehler beim Abrufen der UUID: {err}")
        return None
    
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
        
def add_message_id(uuid, message_id, guild_id):
    cursor = connection.cursor()
    current_datetime = datetime.now()

    insert_query = f"""
    INSERT INTO `{message_database}` (`uuid`, `message_Id`, `guild_id`, `created_at`)
    VALUES (%s, %s, %s, %s)
    """

    data = (uuid, message_id, guild_id, current_datetime)

    try:
        cursor.execute(insert_query, data)
        connection.commit()


    except Exception as e:
        print(f"Fehler beim Einfügen der Daten: {e}")

def get_messages_by_uuid(uuid):
    cursor = connection.cursor()

    query = f"SELECT message_id, guild_id FROM {message_database} WHERE uuid = %s"
    cursor.execute(query, (uuid,))

    result = {message_id: guild_id for message_id, guild_id in cursor.fetchall()}
    return result

def get_servers():
    cursor = connection.cursor(dictionary=True)

    try:
        select_query = f"SELECT guild_id, channel_id, invite FROM {database}"
        cursor.execute(select_query)
        
        results = cursor.fetchall()

        server_list = []
        for result in results:
            server_info = {
                "guildid": result['guild_id'],
                "channelid": result['channel_id'],
                "invite": result['invite']
            }
            server_list.append(server_info)

        return {"servers": server_list}

    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return None
##########################################################################

def generate_random_string():
    characters = string.ascii_letters + string.digits  # enthält Buchstaben (klein und groß) und Zahlen
    random_string = ''.join(random.choice(characters) for _ in range(20))
    return random_string

def get_member_count(server_id, data):
    for guild in data:
        if guild.id == server_id:
            return guild.member_count
    return None

##########################################################################
zeilen_liste = []
with open(emoji_list, 'r', encoding='utf-8') as datei:
    for zeile in datei:
        zeilen_liste.append(zeile.strip())
whitelist_lowercase = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
whitelist_uppercase = [letter.upper() for letter in whitelist_lowercase]
whitelist_numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
whitelist_others = [' ', '#', '+', '*', '~', '_', '-', ',', '.', ':', ';', '!', '"', '§', '$', '%', '&', '/', '(', ')', '=', '?', '{', '}', '[', ']', '^', '°', '²', '³', '@', '€', '<', '>', '\n']
whitelist_special = ['Ä', 'ä', 'Ö', 'ö', 'Ü', 'ü', 'ß']
whitelist_string = [r"'", r'"']

whitelist = whitelist_lowercase + whitelist_uppercase + whitelist_numbers + whitelist_others + whitelist_special + zeilen_liste + whitelist_string
##########################################################################
def block_links(text):
    link_regex1 = re.compile(r'(?:https?://)?[a-z0-9_\-\.]*[a-z0-9_\-]+\.[a-z]{2,}')
    link_regex2 = re.compile(r'(?:https?://)?(?:www.|ptb.|canary.)?(?:discord(?:app)?.(?:(?:com|gg)/(?:invite|servers)/[a-z0-9-_]+)|discord.gg/[a-z0-9-_]+)|(?:https?://)?(?:www.)?(?:dsc.gg|invite.gg+|discord.link|(?:discord.(gg|io|me|li|id))|disboard.org)/[a-z0-9-_/]+')
    link_regex3 = re.compile(r'^#{1,3}\s.*$')

    if link_regex1.search(text) or link_regex2.search(text) or link_regex3.search(text):
        return "|||"
    else:
        return text



def block_swear(text):
    profanity.load_censor_words_from_file(swear_word_list)
    if profanity.contains_profanity(text):
        return ("||")
    else:
        return text


def filter_text(text):
    regex_pattern = '[' + ''.join(map(re.escape, whitelist)) + ']'
    matches = re.findall(regex_pattern, text)

    if len(matches) == len(text):
        return text
    else:
        return "|"
##########################################################################

class global_chat(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        if message.author.bot:
            return

        content_formated = filter_text(message.content)
        conent_anti_swear = block_swear(content_formated)
        conent = block_links(conent_anti_swear)


        if get_globalchat(message.guild.id, message.channel.id):
            if is_user_banned(message.author.id):
                ban_reason = get_ban_reason(message.author.id)
                dm_channel = await message.author.create_dm()

                embed = discord.Embed(title="You are banned", description=f"You have been banned from the Global Chat. If you believe you were banned in error, join the support server and open a ticket.", color=int(color["red_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name="Ban reason", value=f"`{ban_reason}`")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await dm_channel.send(embed=embed, view=BanButtons())
                await message.delete()
                return
        
            permission_level = get_user_permission_level(message.author.id)
            if read_settings_variable("chat_lock") == True and permission_level <4:

                chat_lock_reason = read_settings_variable("chat_lock_reason")
                dm_channel = await message.author.create_dm()

                embed = discord.Embed(title="Chat locked", description=f"The Global Chat is currently locked. If you believe this is an error or if you want to know why the chat is locked, join the support server.", color=int(color["red_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name="Chat Lock reason", value=f"`{chat_lock_reason}`")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await dm_channel.send(embed=embed, view=BanButtons())
                await message.delete()
                return
            else:
                if filter_text(conent) == "|":
                    reason_block = block_reason[conent]
                    dm_channel = await message.author.create_dm()
                    embed = discord.Embed(title="Message blocked", description=f"Your message has been blocked by the Global Chat.", color=int(color["red_color"], 16), timestamp=embed_timestamp)
                    embed.add_field(name="Block reason", value=f"`{reason_block}`")
                    embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                    await dm_channel.send(embed=embed)
                    await message.delete()
                    return
                
                bucket = global_chat_cooldown.get_bucket(message)
                retry_after = bucket.update_rate_limit()
            
                if retry_after:
                    dm_channel = await message.author.create_dm()

                    embed = discord.Embed(title="Cooldown", description=f"The Global Chat bot has a cooldown of 5 seconds to prevent spam. Please wait for this duration before sending a new message.", color=int(color["red_color"], 16), timestamp=embed_timestamp)
                    embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                    await dm_channel.send(embed=embed)
                    await message.delete()
                    return
                
                await self.sendAll(message)

        await self.client.process_commands(message)


    async def sendAll(self, message: discord.Message):
        try:
            conent = f'{message.content}\n⠀'
            author = message.author
            author_url = f"{discord_url}{message.author.id}"
            attachments = message.attachments


            if is_user_in_data(message.author.id):
                role = get_user_role(message.author.id)
                prefix = role_prefix[role]
                color = role_color[role]
        #        embed = discord.Embed(title=f"{prefix}", description=conent, timestamp = embed_timestamp, color=color)

                embed = discord.Embed(title=f"{prefix}", description=f"{conent}", color=color)
            else:
        #        embed = discord.Embed(description=conent, timestamp = embed_timestamp, color=white_color)

                embed = discord.Embed(description=f"{conent}", color=int(color["white_color"], 16))          



            if message.reference:
                uuid = get_uuid_from_message_id(str(message.reference.message_id))
                if uuid != None:
                    replied_message = await message.channel.fetch_message(message.reference.message_id)
                    if replied_message.embeds:  # Überprüfen, ob die Nachricht Embeds hat
                        embed_description = replied_message.embeds[0].description
                        responded_message = embed_description.replace('\n', '')
                        embed.add_field(name='Replied To', value=f'```{responded_message}```', inline=False)


            icon = author.avatar
            embed.set_author(name=author.display_name, icon_url=icon, url=author_url)

            icon_url = standard_server_icon
            icon = message.guild.icon

            data = self.client.guilds 
            server_members = get_member_count(message.guild.id, data)

            if icon:
                icon_url = icon
            embed.set_thumbnail(url=author.avatar)
            embed.set_footer(text=f'{message.guild.name} - {server_members}', icon_url=icon_url)

            links = f'[Support Server]({bot_support_server}) • '
        #    globalchat = get_globalchat(message.guild.id, message.channel.id)
            globalchat = get_globalchat(message.guild.id, message.channel.id)
            if len(globalchat["invite"]) > 0:
                invite = globalchat["invite"]
                if 'discord.gg' not in invite:
                    invite = 'https://discord.gg/{}'.format(invite)
                links += f'[Server Invite]({invite})'

        #    embed.add_field(name='⠀', value='⠀', inline=False)
            embed.add_field(name='Links & Help', value=links, inline=False)

        #    if len(attachments) > 0:
        #        img = attachments[0]
        #        embed.set_image(url=img.url)
            servers = get_servers()

            uuid = generate_random_string()
            while get_messages_by_uuid(uuid) != {}:
                uuid = generate_random_string()

            await message.delete()

            for server in servers["servers"]:
                guild: discord.Guild = self.client.get_guild(int(server["guildid"]))
                if guild:
                    channel: discord.TextChannel = guild.get_channel(int(server["channelid"]))
                    if channel:
                        perms: discord.Permissions = channel.permissions_for(guild.get_member(self.client.user.id))
                        if perms.send_messages:
                            if perms.embed_links and perms.attach_files and perms.external_emojis:
                                sent_message = await channel.send(embed=embed)
                                add_message_id(uuid, sent_message.id, sent_message.guild.id)
                            else:
                                sent_message = await channel.send('{0}: {1}'.format(author.name, conent))
                                add_message_id(uuid, sent_message.id, sent_message.guild.id)
                                await channel.send('Es fehlen einige Berechtigungen. `Nachrichten senden` `Links einbetten` `Datein anhängen` `Externe Emojis verwenden`')
        except Exception as e:
            print(f"{e}")
            return f"{e}"
    
class BanButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)  
        support_server = discord.ui.Button(label='Support Server', style=discord.ButtonStyle.url, url=bot_support_server)
        self.add_item(support_server)
        website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=True)
        self.add_item(website)

async def setup(client:commands.Bot) -> None:
    await client.add_cog(global_chat(client))