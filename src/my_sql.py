import mysql.connector
from datetime import datetime
import os
import json
import asyncio
import threading
from colorama import Back, Fore, Style
import time

from dotenv import load_dotenv
##########################################################################
load_dotenv()

database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')



config_location = os.getenv('config_file')
with open(config_location, 'r', encoding='utf-8') as file:
    config = json.load(file)


database = config["database"]
database = config["database"]
ban_database = config["ban_database"]
user_data_databse = config["user_data_databse"]
message_database = config["message_database"]

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
    
##########################################################################
connection = None 
async def connect():
    global connection  
    while True:
        connection = connect_to_database()
        if connection is not None:
            prfx = (Back.BLACK + Fore.WHITE + Style.BRIGHT + time.strftime("%H:%M:%S", time.gmtime()) + Back.RESET + Fore.BLUE + Style.NORMAL)
            print(prfx + " Error " + Fore.RESET + "Successfully reconnected to the database")
            return connection
        await asyncio.sleep(5)

def check_connection():
    global connection
    while True:
        if connection is None or not connection.is_connected():
            prfx = (Back.BLACK + Fore.WHITE + Style.BRIGHT + time.strftime("%H:%M:%S", time.gmtime()) + Back.RESET + Fore.BLUE + Style.NORMAL)
            print(prfx + " Error " + Fore.RESET + "Lost database connection")
            connection = connect_to_database() 
        time.sleep(5) 


async def main():
    await connect()

##########################################################################
def start_connection_checker():
    connection_checker_thread = threading.Thread(target=check_connection)
    connection_checker_thread.daemon = True
    connection_checker_thread.start()
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

        connection.commit()
        cursor.close()


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

        connection.commit()
        cursor.close()

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

        connection.commit()
        cursor.close()

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

        connection.commit()
        cursor.close()

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

def get_user_permission_level(user_id):
    cursor = connection.cursor(dictionary=True)

    try:
        query = f"SELECT permission_level FROM {user_data_databse} WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()

        connection.commit()
        cursor.close()
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

        connection.commit()
        cursor.close()

    except Exception as e:
        print(f"Fehler beim Einfügen der Daten: {e}")

def get_messages_by_uuid(uuid):
    cursor = connection.cursor()

    query = f"SELECT message_id, guild_id FROM {message_database} WHERE uuid = %s"
    cursor.execute(query, (uuid,))

    result = {message_id: guild_id for message_id, guild_id in cursor.fetchall()}

    connection.commit()
    cursor.close()

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

        connection.commit()
        cursor.close()
        

        return {"servers": server_list}

    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return None

def guild_exists(server_id):
    try:
        cursor = connection.cursor()
        query = f"SELECT * FROM `{database}` WHERE `guild_id` = %s"
        data = (server_id,)
        cursor.execute(query, data)

        result = cursor.fetchone()

        connection.commit()
        cursor.close()
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

        connection.commit()
        cursor.close()
        return output_data

    except mysql.connector.Error as err:
        print(f"Fehler beim Abrufen der Daten: {err}")


def add_user(user_id, role, permission_level):
    try:
        if connection:
            cursor = connection.cursor()
            created_at = datetime.now()

            query = f"INSERT INTO {user_data_databse} (user_id, role, permission_level, created_at) VALUES (%s, %s, %s, %s)"
            data = (user_id, role, permission_level, created_at)

            cursor.execute(query, data)
            connection.commit()
            cursor.close()


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
            cursor.close()

    except Exception as e:
        print(f"Fehler beim Entfernen des Benutzers: {e}")

def get_channel_id_by_guild_id(server_id):
    cursor = connection.cursor()
    query = f"SELECT channel_id FROM {database} WHERE guild_id = %s"
    cursor.execute(query, (server_id,))

    result = cursor.fetchone()

    connection.commit()
    cursor.close()

    if result:
        channel_id = result[0]
        return channel_id
    else:
        return None
    
def load_banned_users():
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT user_id, reason FROM {ban_database}"
        cursor.execute(query)

        result = cursor.fetchall()
        output_data = [{'id': row['user_id'], 'reason': row['reason']} for row in result]

        connection.commit()
        cursor.close()

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
            cursor.close()

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
            cursor.close()

    except Exception as e:
        print(f"Fehler beim Entfernen des Benutzers: {e}")

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
        cursor.close()


    except Exception as e:
        print(f"Fehler beim Einfügen der Daten: {e}")

def remove_guild(guild_id):
    cursor = connection.cursor()

    delete_query = f"DELETE FROM {database} WHERE guild_id = %s"

    try:
        cursor.execute(delete_query, (guild_id,))
        connection.commit()
        cursor.close()


    except Exception as e:
        print(f"Fehler beim Entfernen der Gilde: {e}")