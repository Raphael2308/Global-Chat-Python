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


from datetime import datetime
import pytz
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)
color_location = config["color_file_path"]
with open(color_location, 'r') as file:
    color = json.load(file)

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.now(de)
##########################################################################
permission_error_message = "`❌` You are not staff or your permission level is not high enough."
bot_name = config["bot_name"]
bot_logo_url = config["bot_logo_url"]
admin_guild = config["admin_guild"]
channel_admin_log = config["channel_admin_log"]
channel_staff_log = config["channel_staff_log"]

bot_settings = config["bot_settings_file_path"]
##########################################################################
database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')

database = config["database"]
ban_database = config["ban_database"]
user_data_databse = config["user_data_databse"]
message_database =  config["message_database"]
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

def clear_table(table_name):
    try:
        cursor = connection.cursor()
        sql_query = f"DELETE FROM {table_name}"
        cursor.execute(sql_query)
        connection.commit()
    except Exception as e:
        return (f'Fehler beim Leeren der Tabelle {table_name}: {str(e)}')

##########################################################################
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

def load_data():
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT user_id, role, permission_level FROM {user_data_databse}"
        cursor.execute(query)

        result = cursor.fetchall()
        output_data = [{'user_id': row['user_id'], 'role': row['role'], 'permission_level': row['permission_level']} for row in result]

        return output_data

    except mysql.connector.Error as err:
        print(f"Fehler beim Abrufen der Daten: {err}")

def list_staff_members():
    data = load_data()
    role_prefix_function = {
  "developer": "<:developer:1177680732966101133> Developers",
  "admin": "<:admin:1177681171103096862> Admins",
  "moderator": "<:moderator:1177682704830050444>  Moderators",
  "partner": "<:partner:1179864775761604728>  Partners",
}
    staff_dict = {"developer": [], "admin": [], "moderator": [], "partner": []}

    for entry in data:
        user_id = entry["user_id"]
        role = entry["role"]
        if role == "developer":
            staff_dict["developer"].append(f"- <@{user_id}>")
        elif role == "admin":
            staff_dict["admin"].append(f"- <@{user_id}>")
        elif role == "moderator":
            staff_dict["moderator"].append(f"- <@{user_id}>")
        elif role == "partner":
            staff_dict["partner"].append(f"- <@{user_id}>")

    formatted_text = ""
    for role, members in staff_dict.items():
        if members:
            formatted_text += f"\n{role_prefix_function[role]} - {len(members)}\n"
            formatted_text += "\n".join(members) + "\n"

    return formatted_text

def list_vips():
    data = load_data()
    role_prefix_function = {
        "vip": "<:vip:1177945496401223751> VIPs",
    }
    vips_list = {"vip": []}

    for entry in data:
        user_id = entry["user_id"]
        role = entry["role"]
        if role == "vip":
            vips_list["vip"].append(f"- <@{user_id}>")

    formatted_text = ""
    for role, members in vips_list.items():
        if members:
            formatted_text += f"\n{role_prefix_function[role]} - {len(members)}\n"
            formatted_text += "\n".join(members) + "\n"

    return formatted_text

def add_user(user_id, role, permission_level):
    try:
        if connection:
            cursor = connection.cursor()
            created_at = datetime.now()

            query = f"INSERT INTO {user_data_databse} (user_id, role, permission_level, created_at) VALUES (%s, %s, %s, %s)"
            data = (user_id, role, permission_level, created_at)

            cursor.execute(query, data)
            connection.commit()


    except Exception as e:
        print(f"Fehler beim Hinzufügen des Benutzers: {e}")

def remove_user(user_id):
    try:

        if connection:
            cursor = connection.cursor()

            query = f"DELETE FROM {user_data_databse} WHERE user_id = %s"
            data = (user_id,)

            cursor.execute(query, data)
            connection.commit()

    except Exception as e:
        print(f"Fehler beim Entfernen des Benutzers: {e}")

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
    
def get_channel_id_by_guild_id(server_id):
    cursor = connection.cursor()
    query = f"SELECT channel_id FROM {database} WHERE guild_id = %s"
    cursor.execute(query, (server_id,))

    result = cursor.fetchone()

    if result:
        channel_id = result[0]
        return channel_id
    else:
        return None

def get_messages_by_uuid(uuid):
    cursor = connection.cursor()

    query = f"SELECT message_id, guild_id FROM {message_database} WHERE uuid = %s"
    cursor.execute(query, (uuid,))

    result = {message_id: guild_id for message_id, guild_id in cursor.fetchall()}
    return result

def merge_ids(message_ids_and_guild_ids):
    merged_data = {}

    for message_id, guild_id in message_ids_and_guild_ids.items():
        channel_id = get_channel_id_by_guild_id(guild_id)
        if channel_id is not None:
            merged_data[guild_id] = {'message_id': message_id, 'guild_id': guild_id, 'channel_id': channel_id}
    return merged_data
##########################################################################

##########################################################################
class admin_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="test", description="Test Command")
    async def add_global(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Test", ephemeral=True)



    @app_commands.command(name="staff-list", description="Outputs the list of all staff members")
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(administrator=True)
    async def staff_list(self, interaction: discord.Interaction):
        permission_level = get_user_permission_level(interaction.user.id)
        if permission_level is None:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)
            return  
        if permission_level >= 4:
            formatted_text = list_staff_members()
            formatted_vips = list_vips()
            embed = discord.Embed(title=f"Staff list", description=f"That's a list of all current staff members and VIPs.\n{formatted_text}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n{formatted_vips}", color=int(color["white_color"], 16), timestamp=embed_timestamp)
            embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)

    @app_commands.command(name="set-role", description="Outputs the list of banned users")
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(userid="Enter the User ID of the user")
    @app_commands.describe(role="Enter the role that the user should receive")
    @app_commands.describe(permission_level="Specify the permission level that the user should receive")
    @app_commands.choices(role=[app_commands.Choice(name="default", value="default"), app_commands.Choice(name="VIP", value="vip"), app_commands.Choice(name="Partner", value="partner"),app_commands.Choice(name="Moderator", value="moderator"), app_commands.Choice(name="Admin", value="admin"), app_commands.Choice(name="Developer", value="developer")])
    async def set_role(self, interaction: discord.Interaction, userid: Union[discord.Member, discord.User], role: app_commands.Choice[str] = None, permission_level: int = None):
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
                            log_color = int(color["red_color"], 16)
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
                            log_color = int(color["yellow_color"], 16)
                            break
                    if not user_found:
                        add_user(member_id, user_role, permission_level)
                        log_type = "User Role added."
                        log_color = int(color["light_green_color"], 16)
                
                embed = discord.Embed(title=f"Role Change", description=f"You have successfully changed the role of the user <@{member_id}>.", color=int(color["white_color"], 16), timestamp=embed_timestamp)
                embed.add_field(name="User ID", value=f"`{member_id}`")
                if user_role is None:
                    embed.add_field(name="Role", value=f"`default`")     
                else:
                    embed.add_field(name="Role", value=f"`{user_role}`")              
                embed.add_field(name="Permission Level", value=f"`{permission_level}`")      
                embed.set_footer(text=f"{bot_name}", icon_url=f"{bot_logo_url}")
                await interaction.response.send_message(embed=embed, ephemeral=True)


                if log_type is None or log_color is None:
                    log_embed = discord.Embed(title=f"Role Change", description=f"The following user has been reviewed by <@{interaction.user.id}>.", color=int(color["yellow_color"], 16), timestamp=embed_timestamp)
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

    @app_commands.command(name="clear-database", description="Allows you to clear the Message IDs database")
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
                await interaction.response.send_message(f"`✅` The Message IDs database was successfully cleared.", ephemeral=True)
            except:
                await interaction.response.send_message(f"`❌` An error occurred while clearing the Message IDS table.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)

    @app_commands.command(name="chat-lock", description="Allows you to lock the global chat")
    @app_commands.guilds(admin_guild)
    @app_commands.describe(mode="Choose the chat lock mode")
    @app_commands.describe(reason="Specify the reason for the chat lock")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(mode=[app_commands.Choice(name="On", value="true"), app_commands.Choice(name="Off", value="false")])
    async def server_list(self, interaction: discord.Interaction, mode: app_commands.Choice[str], reason: str = "No reason given"):
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



    @app_commands.command(name="delete-message", description="Allows you to delete a message")
    @app_commands.guilds(admin_guild)
    @app_commands.describe(message_id="Enter the Message ID")
    @app_commands.default_permissions(manage_messages=True)
    async def delete_message(self, interaction: discord.Interaction, message_id: str):
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
                print(merged_ids)
                servers = await self.delete_messages(merged_ids)
                await interaction.edit_original_response(content=f"`✅` Message deleted on `{servers}` servers.")
            except:
                await interaction.edit_original_response(content=f"`❌` An error occurred while deleting the message.")

        else:
            await interaction.response.send_message(f"{permission_error_message}", ephemeral=True)

    async def delete_messages(self, merged_ids):
        try:
            number = 0
            for guild_id, message_info in merged_ids.items():
                result = await self.delete_message(guild_id, message_info['channel_id'], message_info['message_id'])
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
        
    @app_commands.command(name="server-list", description="Outputs the list of banned users")
    @app_commands.guilds(admin_guild)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="Specify how many servers should be displayed")
    @app_commands.choices(amount=[app_commands.Choice(name="10", value="10"), app_commands.Choice(name="20", value="20"), app_commands.Choice(name="50", value="50")])
    async def server_list(self, interaction: discord.Interaction, amount: app_commands.Choice[str] = None):
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
            guilds = sorted(self.client.guilds, key=lambda x: x.member_count, reverse=True)[:server_amount]
            server_count = len(self.client.guilds)

            formatted_list = []
            for guild in guilds:
                check_mark = "`✅`" if guild_exists(guild.id) else "`❌`"
                formatted_list.append(f"{check_mark} **{guild.name}** - `{guild.member_count}`")
                    
            async def get_page(page: int):
                emb = discord.Embed(title=f"Servers ({server_count})", description="These are all servers where the Global Chat bot is, and you can see if they have activated the Global Chat. Use the arrows below to navigate through the pages.\n\n", color=int(color["white_color"], 16))
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
        
async def setup(client:commands.Bot) -> None:
    await client.add_cog(admin_commands(client))