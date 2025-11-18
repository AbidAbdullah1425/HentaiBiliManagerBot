from config import OWNER_ID, LOG_FILE_NAME
from pyrogram import filters, Client
from bot import Bot



@Bot.on_message(filters.user(OWNER_IDS) & filters.command("logs"))
async def get_log_file(client, message):
    try:
        await message.reply_document(document=LOG_FILE_NAME, caption=None)
    except Exception as e:
        logger.error(f"Failed to send log file to OWNER: {e}")
        await message.reply(f"Error:{e}")