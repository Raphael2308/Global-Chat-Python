#THIS IS A SETUP FILE. RUN IT ONLY ONCE AND CONFIGURE THE .ENV FIRST. IT WILL SETUP THE DATABASE
admin_user =  1234 #Enter user ID of the user who should get admin perms (can be changed later with bot commands)

# The name of the tables. Recommended to not change
database = "server_list"
message_database = "message_ids"
user_data_databse = "user_data"
ban_database = "ban_list"

import os
import json
import mysql.connector
from dotenv import load_dotenv

#  Getting the database cridentials to create the tables
database_host = os.getenv('database_host')
database_port = os.getenv('database_port')
database_user = os.getenv('database_user')
database_passwd = os.getenv('database_passwd')
database_database = os.getenv('database_database')
