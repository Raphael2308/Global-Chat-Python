<p align="center"><img src="https://raw.githubusercontent.com/Blackstonecoden/Global-Chat/main/LOGO.png" alt="Global Chat Logo" width="250"></p>
<h1 align="center">Global Chat - Python<br>
	<a href="https://github.com/Blackstonecoden/Global-Chat-Python"><img src="https://img.shields.io/github/stars/blackstonecoden/Global-Chat-Python
    "></a>
	<a href="https://discord.gg/FVQxgBysA7"><img src="https://img.shields.io/discord/1201557790758551574?color=5865f2&label=Discord&style=flat" alt="Discord"></a>
	<br><br>
</h1>

---

## What is the Global Chat BOT?

The Global Chat BOT is a small hobby of mine, where I took a simple base and improved upon it. The original base code is from [CoasterFreak](https://www.youtube.com/watch?v=Ri8RP5AVAFc&list=PLSgiAkLaBUJ8hZUaDs1AcEQ-e1oSBChy1&index=9). IMPORTANT: The code may not necessarily be the best, but it should suffice for a smaller Global Chat for up to 200 servers.

If you'd like to test the features of the Global Chat BOT, feel free to invite the original BOT: [Invite](https://discord.com/oauth2/authorize?client_id=1177590897152622672&permissions=1101659499601&scope=bot%20applications.commands)

---

# Setup

If you want to create your own Global Chat BOT, follow these steps. I will demonstrate the installation using the Pterodactyl software.

### Requirements:

- A server capable of hosting the BOT (Python required)
- A MySQL / MariaDB server

## 1. Download

Click on 'Code' at the top, download as ZIP. On your server panel, create a new server and upload the ZIP file into the root directory. Extract it, and delete the ZIP file. In the directory, there should now be 4 files: .env.example, README.md, .gitignore, LICENSE.md, and a folder named src. You can delete all files except .env.example and the src folder.

## 2. Setup the config files

### 2.1 Setup of the .env file

First, we will edit the .env file. Open the .env.example file and fill in all the information. The comments can assist you. Ensure you input the token, database username, and password, etc., without quotation marks. Once you've filled everything in, rename the file to .env. The file should look something like this:

```.env
TOKEN = ijasodk1239i821
config_file = ./src/config.json

database_host = 192.168.178.11
database_port =  3306
database_user = admin
database_passwd = pasword1234
database_database = globalchat
```
