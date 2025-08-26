from pyrogram import Client
from config import DB_CHANNEL_ID, CREDIT
from bot import Bot
import os
from plugins.progressbar import progress_bar
import time
import asyncio



# send the file to db channel
async def upload(Bot: Client, filepath, message):
    try:
      if not os.path.exists(filepath):
          await message.reply_text(f"File NOT found! {filepath}")
          raise FileNotFoundError(f"File NOT Found {filepath}")

      start = time.time()

      async def prog(current, total):
         await progress_bar(
            current=current,
            total=total,
            start_time=start,
            status="UPLOADING...",
            message=message
         )


    
      send_vid = await Bot.send_video(
          chat_id=DB_CHANNEL_ID,
          video=filepath,
          caption=CREDIT,
          parse_mode="HTML",
          progress=prog
      )

      await message.edit("✌️ Upload Completed")


      return True, send_vid
    except Exception as e:
        return False, str(e)