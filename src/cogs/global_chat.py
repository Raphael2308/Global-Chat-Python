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
import time
import asyncio
import threading
from colorama import Back, Fore, Style

import re
from better_profanity import profanity

from ..my_sql import *

from ..i18n import *
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
bot_support_server = config["bot_support_server"]
bot_website = config["bot_website"]
bot_website_enabled = config["bot_website_enabled"]
standard_server_icon = config["standard_server_icon"]
##########################################################################
swear_word_list = config["swear_file_path"]
emoji_list = config["emoji_file_path"]
color_location = config["color_file_path"]
bot_settings = config["bot_settings_file_path"]
role_location = config["roles_file_path"]
with open(color_location, 'r') as file:
    color = json.load(file)

with open(role_location, 'r') as file:
    roles = json.load(file)

role_prefix = {}
role_color = {}
for role, info in roles.items():
    role_prefix[role] = f"{info['display_name']}"
    role_color[role] = int(info["color"], 16)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)

global_chat_cooldown = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)

discord_url = "https://discordapp.com/users/"
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
def generate_random_string():
    characters = string.ascii_letters + string.digits
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
        return True
    else:
        return False

def block_swear(text):
    profanity.load_censor_words_from_file(swear_word_list)
    if profanity.contains_profanity(text):
        return True
    else:
        return False

def filter_text(text):
    regex_pattern = '[' + ''.join(map(re.escape, whitelist)) + ']'
    matches = re.findall(regex_pattern, text)

    if len(matches) == len(text):
        return False
    else:
        return True
##########################################################################

class global_chat(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if get_globalchat(message.guild.id, message.channel.id):
            if is_user_banned(message.author.id):
                ban_reason = get_ban_reason(message.author.id)
                dm_channel = await message.author.create_dm()

                embed = discord.Embed(title=translator.translate("cogs.global_chat.ban_embed.title"), description=translator.translate("cogs.global_chat.ban_embed.description"), color=int(color["red_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name=translator.translate("cogs.global_chat.ban_embed.ban_reason.name"), value=f"`{ban_reason}`")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await dm_channel.send(embed=embed, view=BanButtons())
                await message.delete()
                return
            
            permission_level = get_user_permission_level(message.author.id)
            if permission_level is None or permission_level <= 15:
                reason_block = None
                if filter_text(message.content):
                    reason_block = translator.translate("cogs.global_chat.block_embed.block_reason.value.filter_text")
                if block_swear(message.content):
                    reason_block = translator.translate("cogs.global_chat.block_embed.block_reason.value.filter_swear")
                if block_links(message.content):
                    reason_block = translator.translate("cogs.global_chat.block_embed.block_reason.value.filter_link")

                if reason_block != None:
                    dm_channel = await message.author.create_dm()
                    embed = discord.Embed(title=translator.translate("cogs.global_chat.block_embed.title"), description=translator.translate("cogs.global_chat.block_embed.description"), color=int(color["red_color"], 16), timestamp=embed_timestamp)
                    embed.add_field(name=translator.translate("cogs.global_chat.block_embed.block_reason.name"), value=f"`{reason_block}`")
                    embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                    await dm_channel.send(embed=embed)
                    await message.delete()
                    return
    
            if permission_level is None:
                permission_level = 0
            if read_settings_variable("chat_lock") == True and permission_level < 4:

                chat_lock_reason = read_settings_variable("chat_lock_reason")
                dm_channel = await message.author.create_dm()

                embed = discord.Embed(title=translator.translate("cogs.global_chat.chat_lock_embed.title"), description=translator.translate("cogs.global_chat.chat_lock_embed.description"), color=int(color["red_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name=translator.translate("cogs.global_chat.chat_lock.lock_reason.name"), value=f"`{chat_lock_reason}`")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await dm_channel.send(embed=embed, view=BanButtons())
                await message.delete()
                return
            else:
                bucket = global_chat_cooldown.get_bucket(message)
                retry_after = bucket.update_rate_limit()
            
                if retry_after:
                    dm_channel = await message.author.create_dm()

                    embed = discord.Embed(title=translator.translate("cogs.global_chat.cooldown_embed.title"), description=translator.translate("cogs.global_chat.cooldown_embed.description"), color=int(color["red_color"], 16), timestamp=embed_timestamp)
                    embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                    await dm_channel.send(embed=embed)
                    await message.delete()
                    return
            if message.content == "":
                dm_channel = await message.author.create_dm()

                embed = discord.Embed(title=translator.translate("cogs.global_chat.image_error_embed.title"), description=translator.translate("cogs.global_chat.image_error_embed.description"), color=int(color["red_color"], 16), timestamp=embed_timestamp)
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
                color_user = role_color[role]
        #        embed = discord.Embed(title=f"{prefix}", description=conent, timestamp = embed_timestamp, color=color)

                embed = discord.Embed(title=f"{prefix}", description=f"{conent}", color=color_user)
            else:
        #        embed = discord.Embed(description=conent, timestamp = embed_timestamp, color=white_color)

                embed = discord.Embed(description=f"{conent}", color=role_color["default"])          



            if message.reference:
                uuid = get_uuid_from_message_id(str(message.reference.message_id))
                if uuid != None:
                    replied_message = await message.channel.fetch_message(message.reference.message_id)
                    if replied_message.embeds:  # Überprüfen, ob die Nachricht Embeds hat
                        embed_description = replied_message.embeds[0].description
                        responded_message = embed_description.replace('\n', '')
                        embed.add_field(name=translator.translate("cogs.global_chat.message.replied_to"), value=f'```{responded_message}```', inline=False)


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
            embed.add_field(name=translator.translate("cogs.global_chat.message.links_help"), value=links, inline=False)

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
        except Exception as e:
            print(f"{e}")
            return f"{e}"
    
class BanButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)  
        support_server = discord.ui.Button(label='Support Server', style=discord.ButtonStyle.url, url=bot_support_server)
        self.add_item(support_server)
        if bot_website_enabled == "True":
            website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=False)
        else:
            website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=True)
        self.add_item(website)

async def setup(client:commands.Bot) -> None:
    await client.add_cog(global_chat(client))