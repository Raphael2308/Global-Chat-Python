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

from cloud import *
from my_sql import *
#from config import *

from dotenv import load_dotenv

#intents = discord.Intents.all()
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)
client.remove_command('help')

##########################################################################
load_dotenv()

TOKEN = os.getenv('TOKEN')

config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)


bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]

admin_guild = config["admin_guild"]
channel_admin_log = config["channel_admin_log"]
channel_staff_log = config["channel_staff_log"]
channel_report_log = config["channel_report_log"]

bot_invite = config["bot_invite"]
bot_support_server =  config["bot_support_server"]
bot_website =  config["bot_website"]

standard_server_icon = config["standard_server_icon"]
icon_announcement = config["icon_announcement"]
icon_important = config["icon_important"]

bot_settings = config["bot_settings_file_path"]
##########################################################################
permission_error_message = "`❌` You are not staff or your permission level is not high enough."
bot_status_1 = f"{bot_name} - The Future"
bot_status_2 = f"{bot_name} - Help with /help"
bot_status_3 = f"{bot_name} -" # The Server-Count Status
##########################################################################
# Don't Change
discord_url = "https://discordapp.com/users/"
##########################################################################

def update_settings_variable(variable_name, new_value):
    try:
        with open(bot_settings, 'r') as file:
            config_data = json.load(file) 
        config_data[variable_name] = new_value  
        with open(bot_settings, 'w') as file:
            json.dump(config_data, file, indent=2)
  
    except FileNotFoundError:
        print('Die Konfigurationsdatei wurde nicht gefunden.')
    except json.JSONDecodeError:
        print('Fehler beim Dekodieren der JSON-Datei.')





##########################################################################













@client.tree.context_menu(name="Delete Message")
@app_commands.default_permissions(manage_messages=True)
async def remove_message(interaction: discord.Interaction, message: discord.Message):
    permission_level = get_user_permission_level(interaction.user.id)
    if permission_level is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return    
    if permission_level >= 4:
        try:            
            await interaction.response.send_message(f"`🔌` Loading...", ephemeral=True)
            uuid = get_uuid_from_message_id(str(message.id))
            if uuid == None:
                await interaction.edit_original_response(content=f"`❌` Error: The message could not be deleted because it is not in the database.")
                return                
            data_messages = get_messages_by_uuid(uuid)
            merged_ids = merge_ids(data_messages)
            servers = await delete_messages(merged_ids)
            await interaction.edit_original_response(content=f"`✅` Message deleted on `{servers}` servers.")
        except:
            await interaction.response.send_message(f"`❌` An error occurred while deleting the message.", ephemeral=True)

    else:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)





@client.tree.command(name="announcement", description="Allows you to send announcements", guild=discord.Object(id=admin_guild))
@app_commands.describe(content="Enter the content of the announcement")
@app_commands.default_permissions(administrator=True)
async def announcement(interaction: discord.Interaction, content: str):
    permission_level = get_user_permission_level(interaction.user.id)
    if permission_level is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return    
    if permission_level >= 10:
        try:
            await interaction.response.send_message(f"`🔌` Loading...", ephemeral=True)
            await send_announcement(content)
            await interaction.edit_original_response(content=f"`✅` Announcement successfully sent.")
        except:
            await interaction.edit_original_response(content=f"`❌` An error occurred while the message was being sent.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)




##########################################################################

#cooldowns = {}

@client.tree.context_menu(name="Report Message")
@app_commands.checks.cooldown(1, 300, key=lambda i: (i.guild_id, i.user.id))
async def report_message(interaction: discord.Interaction, message: discord.Message):
    if is_user_banned(interaction.user.id):
        ban_reason = get_ban_reason(interaction.user.id)
        embed = discord.Embed(title="You are banned", description=f"You have been banned from the Global Chat. If you believe you were banned in error, join the support server and open a ticket.", color=red_color, timestamp=embed_timestamp)
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

    embed = discord.Embed(title=f"Message Reported", description=f"**Message Content:**\n\n```\n{message_description}```\nMessage Author: <@{get_id_by_url(message.embeds[0].author.url)}>\nMessage ID: `{message.id}`\nMessage UUID: `{uuid}`\n\nReportet by: <@{interaction.user.id}>" if message.embeds and message.embeds[0].description else "`❌` Error: No description", color=red_color)
    
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
    
@report_message.error
async def on_test_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"`⌛` Cooldown. Please retry in **{round(error.retry_after, 1)}** seconds.", ephemeral=True)
#        await interaction.response.send_message(str(error), ephemeral=True)

##########################################################################



##########################################################################

global_chat_cooldown = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)

"""@client.event
async def on_message(message):

    # Überprüfe, ob die Nachricht von einem Bot stammt, um Endlosschleifen zu vermeiden
    if message.author.bot:
        return

    # Überprüfe, ob die Nachricht eine Antwort auf eine andere Nachricht ist


    await client.process_commands(message)"""

"""    if message.reference:
        replied_message = await message.channel.fetch_message(message.reference.message_id)
        if replied_message.embeds:  # Überprüfen, ob die Nachricht Embeds hat
            embed_description = replied_message.embeds[0].description
            responded_message = embed_description.replace('\n', '')
            await message.channel.send(f'{message.author.mention}, du hast auf eine Embed-Nachricht geantwortet:\n```{responded_message}```')
        else:
            await message.channel.send(f'{message.author.mention}, du hast auf eine Nachricht ohne Embeds geantwortet:\n```{replied_message.content}```')"""

@client.event
async def on_message(message):
    if message.author.bot:
        return

    bucket = global_chat_cooldown.get_bucket(message)
    retry_after = bucket.update_rate_limit()


    content_formated = filter_text(message.content)
    conent_anti_swear = block_swear(content_formated)
    conent = block_links(conent_anti_swear)


    if get_globalchat(message.guild.id, message.channel.id):
        if is_user_banned(message.author.id):
            ban_reason = get_ban_reason(message.author.id)
            dm_channel = await message.author.create_dm()

            embed = discord.Embed(title="You are banned", description=f"You have been banned from the Global Chat. If you believe you were banned in error, join the support server and open a ticket.", color=red_color, timestamp=embed_timestamp)
            embed.add_field(name="Ban reason", value=f"`{ban_reason}`")
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
            await dm_channel.send(embed=embed, view=BanButtons())
            await message.delete()
            return
    
        permission_level = get_user_permission_level(message.author.id)
        if read_settings_variable("chat_lock") == True and permission_level <4:

            chat_lock_reason = read_settings_variable("chat_lock_reason")
            dm_channel = await message.author.create_dm()

            embed = discord.Embed(title="Chat locked", description=f"The Global Chat is currently locked. If you believe this is an error or if you want to know why the chat is locked, join the support server.", color=red_color, timestamp=embed_timestamp)
            embed.add_field(name="Chat Lock reason", value=f"`{chat_lock_reason}`")
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
            await dm_channel.send(embed=embed, view=BanButtons())
            await message.delete()
            return
        else:


            if retry_after:
                dm_channel = await message.author.create_dm()

                embed = discord.Embed(title="Cooldown", description=f"The Global Chat bot has a cooldown of 5 seconds to prevent spam. Please wait for this duration before sending a new message.", color=red_color, timestamp=embed_timestamp)
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await dm_channel.send(embed=embed)
                await message.delete()
                return

            if filter_text(conent) == "|":
                reason_block = block_reason[conent]
                dm_channel = await message.author.create_dm()
                embed = discord.Embed(title="Message blocked", description=f"Your message has been blocked by the Global Chat.", color=red_color, timestamp=embed_timestamp)
                embed.add_field(name="Block reason", value=f"`{reason_block}`")
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await dm_channel.send(embed=embed)
                await message.delete()
                return
        
            await sendAll(message)

    await client.process_commands(message)



class BanButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)  
        support_server = discord.ui.Button(label='Support Server', style=discord.ButtonStyle.url, url=bot_support_server)
        self.add_item(support_server)
        website = discord.ui.Button(label='Website', style=discord.ButtonStyle.url, url=bot_website, disabled=True)
        self.add_item(website)



##########################################################################



##########################################################################

async def send_announcement(text):
    try:
        conent = text
        author_url = f"{bot_website}"

#        embed = discord.Embed(title="<:admin:1177681171103096862>  Admin", description=f"{conent}\n⠀", color=0xf54651)          
        embed = discord.Embed(description=f"{conent}\n⠀", color=light_blue_color)     
        embed.set_author(name="Announcement", icon_url=bot_logo_url, url=bot_website)

        embed.set_thumbnail(url=icon_announcement)
        embed.set_footer(text=f'Announcement System', icon_url=bot_logo_url)


        links = f'[Support Server]({bot_support_server}) • '
        links += f'[BOT Invite]({bot_invite})'
        embed.add_field(name='Links & Help', value=links, inline=False)

        uuid = generate_random_string()
        while get_messages_by_uuid(uuid) != {}:
            uuid = generate_random_string()

        servers = get_servers()
        for server in servers["servers"]:
            guild: Guild = client.get_guild(int(server["guildid"]))
            if guild:
                channel: TextChannel = guild.get_channel(int(server["channelid"]))
                if channel:
                    perms: Permissions = channel.permissions_for(guild.get_member(client.user.id))
                    if perms.send_messages:
                        if perms.embed_links and perms.attach_files and perms.external_emojis:
#                            sent_message = await channel.send(embed=embed)
                            sent_message = await channel.send(embed=embed)
                            add_message_id(uuid, sent_message.id, sent_message.guild.id)
#                            add_message_id(uuid, sent_message.id, sent_message.guild.id)
                        else:
                            sent_message = await channel.send(embed=embed)
                            add_message_id(uuid, sent_message.id, sent_message.guild.id)
                            await channel.send('Es fehlen einige Berechtigungen. `Nachrichten senden` `Links einbetten` `Datein anhängen` `Externe Emojis verwenden`')
    except Exception as e:
        return f"{e}"

##########################################################################

async def delete_messages(merged_ids):
    try:
        number = 0
        for guild_id, message_info in merged_ids.items():
            result = await delete_message(guild_id, message_info['channel_id'], message_info['message_id'])
            number = number + 1
        return number
    except Exception as e:
        return f"{e}"


async def delete_message(guild_id, channel_id, message_id):
    try:
        guild = client.get_guild(int(guild_id))

        if guild:
            channel = guild.get_channel(int(channel_id))

            if channel:
                try:
                    # Lösche die Nachricht mit der angegebenen ID
                    message = await channel.fetch_message(int(message_id))
                    await message.delete()
                    return (f'Message {message_id} deleted successfully.')
                except discord.NotFound:
                    return (f'Message {message_id} not found.')
                except discord.Forbidden:
                    return (f'Bot has no permission to delete messages in {channel.name}.')
            else:
                return (f'Channel with ID {channel_id} not found in the guild.')
        else:
            return (f'Guild with ID {guild_id} not found.')
    except Exception as e:
        return f"{e}"


##########################################################################

@client.event
async def on_applycation_command_error(interaction, error):
    if isinstance(error, commands.CommandOnCooldown):
        await interaction.response.send_message(error)
    else:
        raise error
    

##########################################################################

@client.event
async def on_ready():
    clear_console()
    prfx = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
    print(prfx + " Logged in as " + Fore.YELLOW + client.user.name)
    print(prfx + " Bot ID " + Fore.YELLOW + str(client.user.id))
    print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
    print(prfx + " Python Version " + Fore.YELLOW + str(platform.python_version()))
    guild_only = await client.tree.sync(guild=discord.Object(id=admin_guild))
    print(prfx + " Guild-Only Slash CMDs Synced " + Fore.YELLOW + str(len(guild_only)) + " Commands")
    synced = await client.tree.sync()
    print(prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) + " Commands")
    client.loop.create_task(status_task())
    client.loop.create_task(database_task())

async def status_task():
    while not client.is_closed():
        await client.change_presence(activity = discord.CustomActivity(name = f"{bot_status_1}"))
        await asyncio.sleep(30)
        await client.change_presence(activity = discord.CustomActivity(name = f"{bot_status_2}"))
        await asyncio.sleep(30)
        await client.change_presence(activity = discord.CustomActivity(name = f"{bot_status_3} {len(client.guilds)} Servers"))
        await asyncio.sleep(30)

async def database_task():
    while not client.is_closed(): 
        keep_alive()    
        await asyncio.sleep(300)

client.run(TOKEN)