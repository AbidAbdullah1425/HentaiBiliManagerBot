#(©)CodeXBotz




import os
import logging
from logging.handlers import RotatingFileHandler



#Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "0")

SESSION = os.environ.get("SESSION", "0")

#Your API ID from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", "26254064"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "72541d6610ae7730e6135af9423b319c")
#Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002689479503"))

#OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", "5296584067"))



DB_CHANNEL_ID = int(os.environ.get("DB_CHANNEL_ID", "-1002689479503"))
POST_CHANNEL_ID = int(os.environ.get("POST_CHANNEL_ID", "-1002372552947"))
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "-1002197279542"))
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Goddo_YatoBot")
CREDIT = os.environ.get("CREDIT", f"<b><a href='tg://user?id={OWNER_ID}'>OnlyNoco</a></b>\n")
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/tmp")
CNL_BUTTON_NAME = os.environ.get("CNL_BUTTON_NAME", "• ᴅᴏᴡɴʟᴏᴀᴅ ‹› ᴡᴀᴛᴄʜ •")
NO_THUMB = "Assist/default_thumb_1.jpg"


GENRE_EMOJIS = {
    "3D": "🖼️",
    "Ahegao": "😵",
    "Anal": "🍑",
    "Blowjob": "💋",
    "Bukakke": "💦",
    "Cosplay": "🎭",
    "Creampie": "🥧",
    "DeepThroat": "😮",
    "Domination": "👑",
    "Facial": "😏",
    "Femdom": "👠",
    "Footjob": "🦶",
    "Gangbang": "👥",
    "Harem": "💃",
    "Housewife": "🏡",
    "Lactation": "🥛",
    "Large Breasts": "🎀",
    "Mary Jane": "🍀",
    "Megane": "👓",
    "MILF": "💁‍♀️",
    "Mind Break": "🧠",
    "Nag": "🗣️",
    "Nuns": "⛪",
    "NTR": "💔",
    "Office Ladies": "👩‍💼",
    "PoRO": "📼",
    "Pink Pineapple": "🍍",
    "Public Sex": "🌆",
    "Queen Bee": "🐝",
    "Rape": "🚫",
    "Rem job": "🍑",
    "Rim job": "🍑",
    "School Girls": "🎒",
    "Short": "📏",
    "Step Sister": "👭",
    "Stocking": "🧦",
    "Tentacles": "🦑",
    "Tits Fuck": "🍒",
    "Train Molestation": "🚆",
    "Tsundere": "😡",
    "Uncensored": "🔓",
    "Urination": "🚽",
    "Vanilla": "🍨",
    "X-Ray": "🔍",
    "Yuri": "🌸",
    "AniMan": "🐰",
    "Bunnywalker": "🐇",
    "Horny Slut": "🔥",
    "Torudaya": "🎌",
    "Shimapan": "🩲",
    "Swimsuit": "👙",
    "Suzuki Mirano": "🎤",
    "Supernatural": "👻",
    "Gold Bear": "🐻‍❄️",
    "Virgins": "🌸",
    "Dark Skin": "🌑",
    "Threesome": "3️⃣",
    "Double Penetration": "➿",
    "Romance": "💖",
    "Super Power": "💥",
    "Majin": "😈",
    "Magical Girls": "✨",
    "Cute & Funny": "😸",
    "Cat Girl": "🐱",
    "Succubus": "🦇",
    "Toys": "🧸",
    "Juicymango": "🥭",
    "Blackmail": "🕳️",
    "Maid": "🧹",
    "Female Teacher": "📚"
}




#Port
PORT = os.environ.get("PORT", "8080")

#Database 
DB_URI = os.environ.get("DB_URI", "mongodb+srv://teamprosperpay:AbidAbdullah199@cluster0.z93fita.mongodb.net/")
DB_NAME = os.environ.get("DATABASE_NAME", "HentaiBiliBot")

#force sub channel id, if you want enable force sub
FORCE_SUB_CHANNEL_1 = int(os.environ.get("FORCE_SUB_CHANNEL_1", "-1002077054432"))
FORCE_SUB_CHANNEL_2 = int(os.environ.get("FORCE_SUB_CHANNEL_2", "-1002003740934"))
FORCE_SUB_CHANNEL_3 = int(os.environ.get("FORCE_SUB_CHANNEL_3", "-1002125561929"))
FORCE_SUB_CHANNEL_4 = int(os.environ.get("FORCE_SUB_CHANNEL_4", "-1002092136573"))

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

#start message
START_MSG = os.environ.get("START_MESSAGE", "Hello {first} I'm a bot who can store files and share it via spacial links")
try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "5296584067").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

#Force sub message 
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "You have to join our Channels First")

#set your Custom Caption here, Keep None for Disable Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot!"

ADMINS.append(OWNER_ID)
ADMINS.append(5296584067)

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
