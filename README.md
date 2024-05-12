<p align="center"><img src="https://raw.githubusercontent.com/Blackstonecoden/Global-Chat/main/LOGO.png" alt="Global Chat Logo" width="200"></p>
<h1 align="center">Global Chat - Python<br>
	<a href="https://github.com/Blackstonecoden/Global-Chat-Python"><img src="https://img.shields.io/github/stars/blackstonecoden/Global-Chat-Python"></a>
	<a href="https://discord.gg/FVQxgBysA7"><img src="https://img.shields.io/discord/1201557790758551574?color=5865f2&label=Discord&style=flat" alt="Discord"></a>
	<br><br>
</h1>

---

## What is the Global Chat BOT?

The Global Chat BOT is a small hobby of mine, where I took a simple base and improved upon it. The original base code is from [CoasterFreak](https://www.youtube.com/watch?v=Ri8RP5AVAFc&list=PLSgiAkLaBUJ8hZUaDs1AcEQ-e1oSBChy1&index=9). And thanks to [Sanamo](https://www.youtube.com/@sanamopy) for some discord.py tutorials. IMPORTANT: The code may not necessarily be the best, but it should suffice for a smaller Global Chat for up to 200 servers.

If you'd like to test the features of the Global Chat BOT, feel free to invite the original BOT: [Invite](https://discord.com/oauth2/authorize?client_id=1177590897152622672&permissions=1101659499601&scope=bot%20applications.commands)

---

# Setup

If you want to create your own Global Chat BOT, follow these steps. I will demonstrate the installation using the Pterodactyl software. Important is that you have a Discord bot set up in advance with the intent `message_content` enabled.

### Requirements:

- A server capable of hosting the BOT (Python required)
- A MySQL / MariaDB server

## 1. Download

Click on releases in the sidebar on the right-hand side, and click on the latest one at the bottom. Under Assets, click on `Global-ChatV?.?.zip`. Now, create a Python server, for example, on Pterodactyl, and move this ZIP file into the root directory. Unarchive this ZIP file now and move the files inside it to the root directory. Delete the ZIP and the unnecessary folder. Now you should have 4 files: a folder named `src`, a file named `.env`, `config.json`, `bot.py`, `setup.py` and `License.md`.

## 2. Setup the config files and libraries

### 2.1 Setup of the .env file

First, we will edit the .env file. Open the .env file and fill in all the information. The comments can assist you. Ensure you input the token, database username, and password, etc., without quotation marks. Once you've filled everything in, save your file. The file should look something like this:

```.env
TOKEN = ijasodk1239i821
config_file = ./config.json

database_host = 192.168.178.11
database_port =  3306
database_user = admin
database_passwd = pasword1234
database_database = globalchat
```

### 2.2 Setup of the config.json file

Next, the config.json will be edited. To do this, open the file `./config.json` and fill in all the information. The tables named database, message_database, etc., are specified in the setup.py file. Save the file. Here is an example of a config.json:

```json
{
  "language": "en",

  "language_file_path": "./src/data",
  "swear_file_path": "./src/messages/swear.txt",
  "bot_settings_file_path": "./src/config/bot_settings.json",
  "emoji_file_path": "./src/messages/emoji.txt",
  "color_file_path": "./src/config/color.json",
  "roles_file_path": "./src/config/roles.json",

  "database": "server_list",
  "message_database": "message_ids",
  "user_data_databse": "user_data",
  "ban_database": "ban_list",

  "bot_name": "Global Chat",
  "bot_status": "Is Global",
  "bot_logo_url": "https://raw.githubusercontent.com/Blackstonecoden/Global-Chat-Python/main/images/LOGO.png",

  "admin_guild": 1821182535732195922,
  "channel_admin_log": 1226092732317868944,
  "channel_staff_log": 1921092252608670088,
  "channel_report_log": 12067942277033260245,

  "bot_invite": "https://discord.com/api/oauth2/authorize?client_id=1177590897152622672&permissions=1101659499601&scope=bot%20applications.commands",
  "bot_support_server": "https://discord.gg/FVQxgBysA7",
  "bot_website": "https://www.discord.com",
  "bot_website_enabled": "True",

  "standard_server_icon": "https://raw.githubusercontent.com/Blackstonecoden/Global-Chat-Python/main/images/BLANK_ICON.jpg"
}
```

Explaination:

```
database: Name of the tables

bot_name: Name of the BOT

bot_status: Custom status. Emojis can be used
bot_logo_url: The logo / profile pictutre of the bot

admin_guild: The admin guild server, where commands like /ban-use or /set-role user can be run (has to be an integer)
channel_admin_log: The log channel where bans are logged (integer)
channe_staff_log: The channel where staff-chanes are logged (with /set-role) (integer)
channel_report_log: The channel where reports are logged (integer)

bot_invite: Invite of the bot. Example: https://discord.com/api/oauth2/authorize?client_id=<YOUR_BOT_ID>&permissions=1101659499601&scope=bot%20applications.commands
bot_support_server: Invite to the support server https://discord.gg/<CODE>
bot_website: Bot website

standard_server_icon: Icon used for servers with no server icon. You don't have to change it
```

### 2.3 Installing all needed libraries

Finally, you need to install all the required libraries. If you have a Pterodactyl server, click on `Server > Startup > Additional Python Packages`, and add the following there: `discord.py mysql-connector python-dotenv colorama schedule pytz better_profanity babel`

If you have a different server, you need to enter `pip install <library>` for each library in the console.

## 3. Additional setup

## 3.1 Emoji setup

To make the role emojis work in the Global Chat, you need to set up specific emojis. First, you need a Discord server, typically the bot support server, where the Bot resides. Then, create 5 emojis, one for each role: Developer, Admin, Moderator, Partner, VIP. Upload these emojis in the Discord server settings, so they should be available in this server. Next, go to a channel and type a backslash, then click on the emoji menu and select the specific role emoji. The message should look like "\:emoji_name:". Send this message. Now the message should look like: `<:admin:1177681171103096862>`. Copy and paste the following into `./src/config/roles.json`. Do this for each role individually.

## 4. Final setup

### 4.1 Database setup

The last thing that needs to be set up now is the database. Navigate to `./setup.py` and edit the `admin_user` variable. This user will have admin privileges and can change the roles and permission level of other users on Discord using /set-role. Execute the file. After that, it will no longer be needed. However, you can keep it in case you lose access to the BOT and need to set a new admin user.

### 4.2 BOT startup

Now you can start the BOT. Make sure you have completed all the preceding steps. If you're using Pterodactyl, go to your `Server > Startup > Bot Py File` and add `./bot.py` there. The BOT should now start without any errors. If there are any issues, feel free to join our [Discord](https://discord.gg/FVQxgBysA7) server and request assistance there.

# Additional notes

## 1. Add custom roles

f you want to add a custom role to the bot, go to ./src/config/roles.json and add a new role to the JSON file. This role should be formatted like this:

```json
{
  "developer": {
    "name": "Developer",
    "display_name": "<:developer:1233439646042554440> DEV",
    "color": "0x5865f2"
  }
}
```

Explaination:

```
developer: The name used in the code, should be unique
name: The name of the role used in the /set-role command
display_name: Name of the role in the global-chat
color: Hex-code that is used in the global-chat messages

```

## 2. Permission system

The permission system is very simple. There are roles and permission levels. With `/set-role <user> <role> <permission_level>`, you can set a user's role and permission level (this command can only be executed in the admin guild). It's important to note that the role is purely cosmetic, and the permission level is what matters. Anyone with permission level 4 or higher can delete messages in the global chat, view the server list, and view the staff list. Anyone with permission level 10 or higher has access to all bot functions. This includes modifying roles of others (even if their permission level is higher than their), clearing the message database (this should be done every 3 weeks), and locking the global chat.
