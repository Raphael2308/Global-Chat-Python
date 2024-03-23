import os
import json
import pytz
import datetime
import re
import random
import string
from better_profanity import profanity

from dotenv import load_dotenv
##########################################################################
load_dotenv()


config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)

filepath = config["swear_file_path"]
zeilen_liste = []
with open(filepath, 'r', encoding='utf-8') as datei:
    for zeile in datei:
        zeilen_liste.append(zeile.strip())

##########################################################################

de = pytz.timezone('Europe/Berlin')
embed_timestamp = datetime.datetime.now(de)

swear_word_list = r"C:\Users\josef\Visual Studio Code\Modifizierte\1 - Discord BOTs\Global Chat\V2\swear.txt"
whitelist_lowercase = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
whitelist_uppercase = [letter.upper() for letter in whitelist_lowercase]
whitelist_numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
whitelist_others = [' ', '#', '+', '*', '~', '_', '-', ',', '.', ':', ';', '!', '"', '§', '$', '%', '&', '/', '(', ')', '=', '?', '{', '}', '[', ']', '^', '°', '²', '³', '@', '€', '<', '>', '\n']
whitelist_special = ['Ä', 'ä', 'Ö', 'ö', 'Ü', 'ü', 'ß']
whitelist_string = [r"'", r'"']

whitelist = whitelist_lowercase + whitelist_uppercase + whitelist_numbers + whitelist_others + whitelist_special + zeilen_liste + whitelist_string

##########################################################################


bann_list = "banned_users.json"
permission_list = "user_data.json"


block_reason = {
    "|": "Banned Unicode character",
    "||": "Swear word blocked",
    "|||": "Link blocked"
}

role_prefix = {
  "developer": "<:developer:1177680732966101133>  DEV",
  "admin": "<:admin:1177681171103096862>  Admin",
  "moderator": "<:moderator:1177682704830050444>  MOD",
  "partner": "<:partner:1179864775761604728>  Partner",
  "vip": "<:vip:1177945496401223751>  VIP",
  "default": ""
}

role_color = {
  "developer": 0x5865f2,
  "admin": 0xf54651,
  "moderator": 0xfc964b,
  "partner": 0x4dbc62,
  "vip": 0xfbb848,
  "default": 0xffffff
}


##########################################################################

white_color = 0xffffff

red_color = 0xff6a6a
orange_color = 0xffa66a
yellow_color = 0xfffa6a
light_green_color = 0x6aff9b
dark_blue_color = None
blue_color = 0x6a7bff
light_blue_color = 0x6adfff
purple_color = 0x856aff

##########################################################################

def get_id_by_url(url):
    index = url.rfind('/')
    if index != -1:
        return url[index + 1:]
    else:
        return url

def get_member_count(server_id, data):
    for guild in data:
        if guild.id == server_id:
            return guild.member_count
    return None


def block_links(text):
    link_regex1 = re.compile(r'(?:https?://)?[a-z0-9_\-\.]*[a-z0-9_\-]+\.[a-z]{2,}')
    link_regex2 = re.compile(r'(?:https?://)?(?:www.|ptb.|canary.)?(?:discord(?:app)?.(?:(?:com|gg)/(?:invite|servers)/[a-z0-9-_]+)|discord.gg/[a-z0-9-_]+)|(?:https?://)?(?:www.)?(?:dsc.gg|invite.gg+|discord.link|(?:discord.(gg|io|me|li|id))|disboard.org)/[a-z0-9-_/]+')
    link_regex3 = re.compile(r'^#{1,3}\s.*$')

    if link_regex1.search(text) or link_regex2.search(text) or link_regex3.search(text):
        return "|||"
    else:
        return text



def block_swear(text):
    profanity.load_censor_words_from_file(swear_word_list)
    if profanity.contains_profanity(text):
        return ("||")
    else:
        return text


def filter_text(text):
    regex_pattern = '[' + ''.join(map(re.escape, whitelist)) + ']'
    matches = re.findall(regex_pattern, text)

    if len(matches) == len(text):
        return text
    else:
        return "|"

def decode_emojis(text):
    pass


##########################################################################

def generate_random_string():
    characters = string.ascii_letters + string.digits  # enthält Buchstaben (klein und groß) und Zahlen
    random_string = ''.join(random.choice(characters) for _ in range(20))
    return random_string

##########################################################################

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

##########################################################################