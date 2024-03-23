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
@client.tree.command(name="server-list", description="Outputs the list of banned users", guild=discord.Object(id=admin_guild))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(amount="Specify how many servers should be displayed")
@app_commands.choices(amount=[app_commands.Choice(name="10", value="10"), app_commands.Choice(name="20", value="20"), app_commands.Choice(name="50", value="50")])
async def server_list(interaction: discord.Interaction, amount: app_commands.Choice[str] = None):
    L = 10 #Length
    permission_level = get_user_permission_level(interaction.user.id)
    if permission_level is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return  
    if permission_level >= 4:
        if amount is None:
            server_amount = 10
        else:
            server_amount = int(amount.value)
        guilds = sorted(client.guilds, key=lambda x: x.member_count, reverse=True)[:server_amount]
        server_count = len(client.guilds)

        formatted_list = []
        for guild in guilds:
            check_mark = "`✅`" if guild_exists(guild.id) else "`❌`"
            formatted_list.append(f"{check_mark} **{guild.name}** - `{guild.member_count}`")
                  
        async def get_page(page: int):
            emb = discord.Embed(title=f"Servers ({server_count})", description="These are all servers where the Global Chat bot is, and you can see if they have activated the Global Chat. Use the arrows below to navigate through the pages.\n\n", color=white_color)
            offset = (page-1) * L
            for server in formatted_list[offset:offset+L]:
                emb.description += f"{server}\n"
#            emb.set_author(name=f"Requested by {interaction.user}")
            n = Pagination.compute_total_pages(len(formatted_list), L)
            emb.set_footer(text=f"{bot_name} - Page {page} from {n}", icon_url=f"{bot_logo_url}")
#            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n

        await Pagination(interaction, get_page).navegate()
    else:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)


@client.tree.command(name="staff-list", description="Outputs the list of all staff members", guild=discord.Object(id=admin_guild))
@app_commands.default_permissions(administrator=True)
async def staff_list(interaction: discord.Interaction):
    permission_level = get_user_permission_level(interaction.user.id)
    if permission_level is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return  
    if permission_level >= 4:
        formatted_text = list_staff_members()
        formatted_vips = list_vips()
        embed = discord.Embed(title=f"Staff list", description=f"That's a list of all current staff members and VIPs.\n{formatted_text}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n{formatted_vips}", color=white_color, timestamp=embed_timestamp)
        embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)


@client.tree.command(name="set-role", description="Outputs the list of banned users", guild=discord.Object(id=admin_guild))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(userid="Enter the User ID of the user")
@app_commands.describe(role="Enter the role that the user should receive")
@app_commands.describe(permission_level="Specify the permission level that the user should receive")
@app_commands.choices(role=[app_commands.Choice(name="default", value="default"), app_commands.Choice(name="VIP", value="vip"), app_commands.Choice(name="Partner", value="partner"),app_commands.Choice(name="Moderator", value="moderator"), app_commands.Choice(name="Admin", value="admin"), app_commands.Choice(name="Developer", value="developer")])
async def set_role(interaction: discord.Interaction, userid: Union[discord.Member, discord.User], role: app_commands.Choice[str] = None, permission_level: int = None):
    permission = get_user_permission_level(interaction.user.id)
    if permission is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return
    if permission >= 9:
        try:
            member_id = str(userid.id)
            if role is None or role.value == "default":
                data = load_data()
                user_found = False  # Flag to check if the user is found in the data
                for user_data in data:
                    if user_data['user_id'] == member_id:
                        remove_user(member_id)
                        user_role = "default"
                        user_found = True
                        log_type = "User Role removed."
                        log_color = red_color
                        break

                if not user_found:
                    await interaction.response.send_message(content=f"You cannot move <@{member_id}> to the default group as they are already in the default group.", ephemeral=True)
                    return

            else:
                if permission_level is None:
                    permission_level = 0

                user_role = role.value
                data = load_data()
                user_found = False
                for user_data in data:
                    if user_data['user_id'] == member_id:
                        remove_user(member_id)
                        add_user(member_id, user_role, permission_level)
                        user_found = True
                        log_type = "User Role changed"
                        log_color = yellow_color
                        break
                if not user_found:
                    add_user(member_id, user_role, permission_level)
                    log_type = "User Role added."
                    log_color = light_green_color
            
            embed = discord.Embed(title=f"Role Change", description=f"You have successfully changed the role of the user <@{member_id}>.", color=white_color, timestamp=embed_timestamp)
            embed.add_field(name="User ID", value=f"`{member_id}`")
            if user_role is None:
                embed.add_field(name="Role", value=f"`default`")     
            else:
                embed.add_field(name="Role", value=f"`{user_role}`")              
            embed.add_field(name="Permission Level", value=f"`{permission_level}`")      
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
            await interaction.response.send_message(embed=embed, ephemeral=True)


            if log_type is None or log_color is None:
                log_embed = discord.Embed(title=f"Role Change", description=f"The following user has been reviewed by <@{interaction.user.id}>.", color=yellow_color, timestamp=embed_timestamp)
            else:
                log_embed = discord.Embed(title=f"{log_type}", description=f"The following user has been reviewed by <@{interaction.user.id}>.", color=log_color, timestamp=embed_timestamp)

            log_embed.add_field(name="User", value=f"<@{member_id}>")

            if user_role is None:
                log_embed.add_field(name="Role", value=f"`default`")     
            else:
                log_embed.add_field(name="Role", value=f"`{user_role}`")  

            log_embed.add_field(name="Permission Level", value=f"`{permission_level}`")  
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

            channel = interaction.client.get_channel(channel_staff_log)
            await channel.send(embed=log_embed)

        except:
            await interaction.response.send_message(content="An error occurred.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)



@client.tree.command(name="delete-message", description="Allows you to delete a message", guild=discord.Object(id=admin_guild))
@app_commands.describe(message_id="Enter the Message ID")
@app_commands.default_permissions(manage_messages=True)
async def delete_message(interaction: discord.Interaction, message_id: str):
    permission_level = get_user_permission_level(interaction.user.id)
    if permission_level is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return    
    if permission_level >= 4:
        try:            
            await interaction.response.send_message(f"`🔌` Loading...", ephemeral=True)
            uuid = get_uuid_from_message_id(str(message_id))
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


@client.tree.command(name="clear-database", description="Allows you to clear the Message IDs database", guild=discord.Object(id=admin_guild))
@app_commands.default_permissions(administrator=True)
async def clear_database(interaction: discord.Interaction):
    permission_level = get_user_permission_level(interaction.user.id)
    if permission_level is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return    
    if permission_level >= 10:
        try:
            clear_table(message_database)
            await interaction.response.send_message(f"`✅` The Message IDs database was successfully cleared.", ephemeral=True)
        except:
            await interaction.response.send_message(f"`❌` An error occurred while clearing the Message IDS table.", ephemeral=True)
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


@client.tree.command(name="chat-lock", description="Allows you to lock the global chat", guild=discord.Object(id=admin_guild))
@app_commands.describe(mode="Choose the chat lock mode")
@app_commands.describe(reason="Specify the reason for the chat lock")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(mode=[app_commands.Choice(name="On", value="true"), app_commands.Choice(name="Off", value="false")])
async def server_list(interaction: discord.Interaction, mode: app_commands.Choice[str], reason: str = "No reason given"):
    permission_level = get_user_permission_level(interaction.user.id)
    if permission_level is None:
        await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
        return    
    if permission_level >= 10:
        try:
            await interaction.response.send_message(f"`🔌` Loading...", ephemeral=True)
            if mode.value == "true":
                update_settings_variable("chat_lock_reason", reason)
            else:
                update_settings_variable("chat_lock_reason", "None")

            update_settings_variable("chat_lock", mode.value)
            
            if mode.value == "true":
                await interaction.edit_original_response(content=f"`🔒` The global chat has been successfully locked.")
            else:
                await interaction.edit_original_response(content=f"`🔓` The global chat has been successfully unlocked.")
        except:
            await interaction.edit_original_response(content=f"`❌` An error occurred while locking the chat.")
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

class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1
        super().__init__(timeout=100)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navegate(self):
        emb, self.total_pages = await self.get_page(self.index)
        if self.total_pages == 1:
            await self.interaction.response.send_message(embed=emb, ephemeral=True)
        elif self.total_pages > 1:
            self.update_buttons()
            await self.interaction.response.send_message(embed=emb, view=self, ephemeral=True)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == 1
        self.children[2].disabled = self.index == self.total_pages
        self.children[3].disabled = self.index == self.total_pages


#    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    @discord.ui.button(label="|<", style=discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.Button):
        self.index = 1
        await self.edit_page(interaction)

#    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.green)
    @discord.ui.button(label="<", style=discord.ButtonStyle.green)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

#    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.green)
    @discord.ui.button(label=">", style=discord.ButtonStyle.green)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

#    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    @discord.ui.button(label=">|", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        self.index = self.total_pages
        await self.edit_page(interaction)


    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1

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



async def sendAll(message: Message):
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

            embed = discord.Embed(description=f"{conent}", color=white_color)          



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

        data = client.guilds
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
            guild: Guild = client.get_guild(int(server["guildid"]))
            if guild:
                channel: TextChannel = guild.get_channel(int(server["channelid"]))
                if channel:
                    perms: Permissions = channel.permissions_for(guild.get_member(client.user.id))
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