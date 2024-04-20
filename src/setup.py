#THIS IS A SETUP FILE. RUN IT ONLY ONCE AND CONFIGURE THE .ENV FIRST. IT WILL SETUP THE DATABASE
admin_user =  1234 #Enter user ID of the user who should get admin perms (can be changed later with bot commands)

# The name of the tables. Recommended to not change. If you wan't to change it, change it in config.json too
database = "server_list_test"
message_database = "message_ids"
user_data_databse = "user_data"
ban_database = "ban_list"

import os
import json
import mysql.connector
from dotenv import load_dotenv

#  Getting the database cridentials to create the tables
load_dotenv()
database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')

try:
    connection = mysql.connector.connect(
        host=database_host,
        port=database_port,
        user=database_user,
        passwd=database_passwd,
        database=database_database
    )
    cursor = connection.cursor()
except mysql.connector.Error as err:
    print(f"Error: {err}")

def create_table(query):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query)

        connection.commit()
    except:
        print("Error: Failed to create database")
    
create_table(f"""
CREATE TABLE IF NOT EXISTS `{database}` (
  `guild_id` varchar(50) NOT NULL DEFAULT '-1',
  `channel_id` varchar(50) NOT NULL DEFAULT '-1',
  `invite` varchar(50) NOT NULL DEFAULT 'None',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`guild_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
""")

create_table(f"""
CREATE TABLE `{message_database}` (
  `uuid` varchar(25) NOT NULL DEFAULT '-1',
  `message_id` varchar(50) NOT NULL DEFAULT 'None',
  `guild_id` varchar(50) NOT NULL DEFAULT 'None',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
""")

create_table(f"""
CREATE TABLE `{user_data_databse}` (
  `user_id` varchar(50) NOT NULL DEFAULT '-1',
  `role` varchar(50) NOT NULL DEFAULT 'default',
  `permission_level` varchar(50) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
""")

create_table(f"""
CREATE TABLE `{ban_database}` (
  `user_id` varchar(50) NOT NULL DEFAULT '-1',
  `reason` varchar(50) NOT NULL DEFAULT 'None',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
""")