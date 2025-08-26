from pyrogram import Client
from config import DB_CHANNEL_ID, CREDIT
from bot import Bot
import os

# send the file to db channel
async def upload(Bot: Client, filepath, caption, message):
    try:
      if not os.path.exists(filepath):
          await message.reply_text(f"File NOT found! {filepath}")
          raise FileNotFoundError(f"File NOT Found {filepath}")
    
      send_vid = await Bot.send_video(
          chat_id=DB_CHANNEL_ID,
          video=filepath,
          caption=caption,
          parse_mode="HTML"
      )
      return True, send_vid
    except Exception as e:
        return False, str(e)