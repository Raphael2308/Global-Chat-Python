import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import json
import mysql.connector
from typing import Callable, Optional
from typing import Union
from discord.app_commands import Parameter
from ...my_sql import *

from datetime import datetime
import pytz

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

role_location = config["roles_file_path"]
with open(role_location, 'r') as file:
    roles = json.load(file)

role_prefix = {}
role_color = {}
for role, info in roles.items():
    role_prefix[role] = f"{info['display_name']}"
    role_color[role] = int(info["color"], 16)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)
##########################################################################
language = config["language"]
language_file_path = config["language_file_path"]

translator = Translator(language_file_path, language)
permission_error_message = translator.translate("cogs.admin_commands.permission_error_message")
##########################################################################
bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]
admin_guild = config["admin_guild"]
channel_admin_log = config["channel_admin_log"]
channel_staff_log = config["channel_staff_log"]

bot_settings = config["bot_settings_file_path"]
##########################################################################
role_choices = [app_commands.Choice(name=info["name"], value=role) for role, info in roles.items()]
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
def list_staff_members():
    data = load_data()
    staff_dict = {role: [] for role in roles if role != "default"}

    for entry in data:
        user_id = entry["user_id"]
        role = entry["role"]
        if role in staff_dict:
            staff_dict[role].append(f"- <@{user_id}>")
        
    formatted_text = ""
    for role, members in staff_dict.items():
        if members:
            formatted_text += f"\n{role_prefix.get(role, '')} - {len(members)}\n"
            formatted_text += "\n".join(members) + "\n"

    return formatted_text

def merge_ids(message_ids_and_guild_ids):
    merged_data = {}

    for message_id, guild_id in message_ids_and_guild_ids.items():
        channel_id = get_channel_id_by_guild_id(guild_id)
        if channel_id is not None:
            merged_data[guild_id] = {'message_id': message_id, 'guild_id': guild_id, 'channel_id': channel_id}
    return merged_data
##########################################################################
class admin_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        self.ctx_menu = app_commands.ContextMenu(name='Delete Message', callback=self.remove_message)
        self.client.tree.add_command(self.ctx_menu) 


    @app_commands.command(name="staff-list", description=translator.translate("command.staff_list.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(administrator=True)
    async def staff_list(self, interaction: discord.Interaction):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return  
        if permission_level >= 4:
            formatted_text = list_staff_members()
#            formatted_vips = list_vips()
#            embed = discord.Embed(title=f"Staff list", description=f"That's a list of all current staff members.\n{formatted_text}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n{formatted_vips}", color=int(color["white_color"], 16), timestamp=embed_timestamp)
            embed = discord.Embed(title=translator.translate("command.staff_list.embed.title"), description=translator.translate("commands.staff_list.embed.description", formatted_text=formatted_text), color=int(color["white_color"], 16), timestamp=embed_timestamp)
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)

    @app_commands.command(name="set-role", description=translator.translate("command.set_role.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(userid=translator.translate("command.set_role.parameter.userid"))
    @app_commands.describe(role=translator.translate("command.set_role.parameter.role"))
    @app_commands.describe(permission_level=translator.translate("command.set_role.parameter.permission_level"))
    @app_commands.choices(role=role_choices)
    async def set_role(self, interaction: discord.Interaction, userid: Union[discord.Member, discord.User], role: app_commands.Choice[str] = None, permission_level: int = None):
        permission = get_user_permission_level(interaction.user.id)
        if permission is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return
        if permission >= 10:
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
                            log_type = translator.translate("command.set_role.log_embed.title.role_removed")
                            log_color = int(color["red_color"], 16)
                            break

                    if not user_found:
                        await interaction.response.send_message(content=translator.translate("command.set_role.error.user", member_id=member_id), ephemeral=True)
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
                            log_type = translator.translate("command.set_role.log_embed.title.role_changed")
                            log_color = int(color["yellow_color"], 16)
                            break
                    if not user_found:
                        add_user(member_id, user_role, permission_level)
                        log_type = translator.translate("command.set_role.log_embed.title.role_added")
                        log_color = int(color["light_green_color"], 16)
                
                embed = discord.Embed(title=translator.translate("command.set_role.embed.title"), description=translator.translate("command.set_role.embed.description", member_id=member_id), color=int(color["white_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name=translator.translate("command.set_role.embed.user_id.name"), value=f"`{member_id}`")
                if user_role is None:
                    embed.add_field(name=translator.translate("command.set_role.embed.role.name"), value=f"`default`")     
                else:
                    embed.add_field(name=translator.translate("command.set_role.embed.role.name"), value=f"`{user_role}`")              
                embed.add_field(name=translator.translate("command.set_role.embed.permission_level.name"), value=f"`{permission_level}`")      
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)


                if log_type is None or log_color is None:
                    log_embed = discord.Embed(title=translator.translate("command.set.role.log_embed.title.role_change"), description=translator.translate("command.set_role.log_embed.description", user_id=interaction.user.id), color=int(color["yellow_color"], 16), timestamp=embed_timestamp)
                else:
                    log_embed = discord.Embed(title=f"{log_type}", description=translator.translate("command.set_role.log_embed.description", user_id=interaction.user.id), color=log_color, timestamp=embed_timestamp)

                log_embed.add_field(name=translator.translate("command.set_role.log_embed.user.name"), value=f"<@{member_id}>")

                if user_role is None:
                    log_embed.add_field(name=translator.translate("command.set_role.log_embed.role.name"), value=f"`default`")     
                else:
                    log_embed.add_field(name=translator.translate("command.set_role.log_embed.role.name"), value=f"`{user_role}`")  

                log_embed.add_field(name=translator.translate("command.set_role.log_embed.permission_level.name"), value=f"`{permission_level}`")  
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")

                channel = interaction.client.get_channel(channel_staff_log)
                await channel.send(embed=log_embed)

            except:
                await interaction.response.send_message(content=translator.translate("command.set_role.error"), ephemeral=True)
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)

    @app_commands.command(name="clear-database", description=translator.translate("command.clear_table.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(administrator=True)
    async def clear_database(self, interaction: discord.Interaction):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return    
        if permission_level >= 10:
            try:
                clear_table(message_database)
                await interaction.response.send_message(content=translator.translate("command.clear_database.message.succes"), ephemeral=True)
            except:
                await interaction.response.send_message(content=translator.translate("command.clear_database.message.error"), ephemeral=True)
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)

    @app_commands.command(name="chat-lock", description=translator.translate("command.chat_lock.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.describe(mode=translator.translate("command.chat_lock.parameter.mode"))
    @app_commands.describe(reason=translator.translate("command.chat_lock.parameter.reason"))
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(mode=[app_commands.Choice(name=translator.translate("command.chat_lock.parameter.mode.on"), value="true"), app_commands.Choice(name=translator.translate("command.chat_lock.parameter.mode.off"), value="false")])
    async def chat_lock(self, interaction: discord.Interaction, mode: app_commands.Choice[str], reason: str = "No reason given"):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return    
        if permission_level >= 10:
            try:
                await interaction.response.send_message(content=translator.translate("command.chat_lock.message.loading"), ephemeral=True)
                if mode.value == "true":
                    update_settings_variable("chat_lock_reason", reason)
                else:
                    update_settings_variable("chat_lock_reason", "None")

                update_settings_variable("chat_lock", mode.value)
                
                if mode.value == "true":
                    await interaction.edit_original_response(content=translator.translate("command.chat_lock.message.locked"))
                else:
                    await interaction.edit_original_response(content=translator.translate("command.chat_lock.message.unlocked"))
            except:
                await interaction.edit_original_response(content=translator.translate("command.chat_lock.message.error"))
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)



    @app_commands.command(name="delete-message", description=translator.translate("command.delete_message.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.describe(message_id=translator.translate("command.delete_message.parameter.message_id"))
    @app_commands.default_permissions(manage_messages=True)
    async def delete_message(self, interaction: discord.Interaction, message_id: str):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return    
        if permission_level >= 4:
            try:            
                await interaction.response.send_message(content=translator.translate("command.delete_message.message.loading"), ephemeral=True)
                uuid = get_uuid_from_message_id(str(message_id))
                if uuid == None:
                    await interaction.edit_original_response(content=translator.translate("command.delete_message.error.not_in_database"))
                    return                
                data_messages = get_messages_by_uuid(uuid)
                merged_ids = merge_ids(data_messages)
                servers = await delete_messages(self, merged_ids)
                await interaction.edit_original_response(content=translator.translate("command.delete_message.message.succes", servers=servers))
            except:
                await interaction.edit_original_response(content=translator.translate("command.delete_message.message.error"))

        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)




#    @app_commands.context_menu(name="Delete Message")
    @app_commands.default_permissions(manage_messages=True)
    async def remove_message(self, interaction: discord.Interaction, message: discord.Message):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return    
        if permission_level >= 4:
            try:            
                await interaction.response.send_message(content=translator.translate("command.delete_message.message.loading"), ephemeral=True)
                uuid = get_uuid_from_message_id(str(message.id))
                if uuid == None:
                    await interaction.edit_original_response(content=translator.translate("command.delete_message.error.not_in_database"))
                    return                
                data_messages = get_messages_by_uuid(uuid)
                merged_ids = merge_ids(data_messages)
                servers = await delete_messages(self, merged_ids)
                await interaction.edit_original_response(content=translator.translate("command.delete_message.message.succes", servers=servers))
            except:
                await interaction.edit_original_response(content=translator.translate("command.delete_message.message.error"))

        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)


        
    @app_commands.command(name="server-list", description=translator.translate("command.server_list.description"))
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount=translator.translate("command.server_list.parameter.amount"))
    @app_commands.choices(amount=[app_commands.Choice(name="50", value="50"), app_commands.Choice(name="100", value="100"), app_commands.Choice(name="200", value="200")])
    async def server_list(self, interaction: discord.Interaction, amount: app_commands.Choice[str] = None):
        L = 10 #Length
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return  
        if permission_level >= 4:
            if amount is None:
                guilds = sorted(self.client.guilds, key=lambda x: x.member_count, reverse=True)
            else:
                server_amount = int(amount.value)
                guilds = sorted(self.client.guilds, key=lambda x: x.member_count, reverse=True)[:server_amount]

            server_count = len(self.client.guilds)

            formatted_list = []
            for guild in guilds:
                check_mark = "`✅`" if guild_exists(guild.id) else "`❌`"
                formatted_list.append(f"{check_mark} **{guild.name}** - `{guild.member_count}`")
                    
            async def get_page(page: int):
                emb = discord.Embed(title=translator.translate("command.server_list.embed.title", server_count=server_count), description=translator.translate("command.server_list.embed.description"), color=int(color["white_color"], 16))
                offset = (page-1) * L
                for server in formatted_list[offset:offset+L]:
                    emb.description += f"{server}\n"
    #            emb.set_author(name=f"Requested by {interaction.user}")
                n = Pagination.compute_total_pages(len(formatted_list), L)
                emb.set_footer(text=translator.translate("command.server_list.embed.footer", bot_name=bot_name, page=page, n=n), icon_url=f"{bot_logo_url}")
    #            emb.set_footer(text=f"Page {page} from {n}")
                return emb, n

            await Pagination(interaction, get_page).navegate()
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)


async def delete_messages(self, merged_ids):
    try:
        number = 0
        for guild_id, message_info in merged_ids.items():
            result = await delete_message(self, guild_id, message_info['channel_id'], message_info['message_id'])
            number = number + 1
        return number
    except Exception as e:
        return f"{e}"


async def delete_message(self, guild_id, channel_id, message_id):
    try:
        guild = self.client.get_guild(int(guild_id))

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
        
async def setup(client:commands.Bot) -> None:
    await client.add_cog(admin_commands(client))