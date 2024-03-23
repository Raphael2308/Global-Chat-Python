import mysql.connector
from datetime import datetime
import os
import json

from dotenv import load_dotenv
##########################################################################
load_dotenv()

database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')

config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)


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
        print("Verbindung erfolgreich hergestellt!")
        return connection
    except mysql.connector.Error as err:
        print(f"Fehler bei der Verbindung: {err}")
        return None

def keep_alive():
    try:
        if not connection.is_connected():
            connection.reconnect()
    except Exception as e:
        print(f"Fehler bei der Überprüfung der Datenbankverbindung: {e}")


connection = connect_to_database()
cursor = connection.cursor()

##########################################################################
def clear_table(table_name):
    try:
        cursor = connection.cursor()
        sql_query = f"DELETE FROM {table_name}"
        cursor.execute(sql_query)
        connection.commit()
    except Exception as e:
        return (f'Fehler beim Leeren der Tabelle {table_name}: {str(e)}')

##########################################################################

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


def merge_ids(message_ids_and_guild_ids):
    merged_data = {}

    for message_id, guild_id in message_ids_and_guild_ids.items():
        channel_id = get_channel_id_by_guild_id(guild_id)
        if channel_id is not None:
            merged_data[guild_id] = {'message_id': message_id, 'guild_id': guild_id, 'channel_id': channel_id}
    return merged_data


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
    




##########################################################################



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



##########################################################################



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
