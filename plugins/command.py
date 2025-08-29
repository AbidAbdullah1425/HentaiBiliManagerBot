import os 
import random
import string
import time
from bot import Bot
from config import OWNER_ID, DOWNLOAD_DIR, CREDIT, DB_CHANNEL_ID, POST_CHANNEL_ID, LOG_CHANNEL_ID, LOGGER
from pyrogram import Client, filters
from plugins.download import download
from plugins.upload import upload
from plugins.link_gen import link_gen
from plugins.ffmpeg_thumb import generate_video_thumbnail
from datetime import datetime
import logging
import pytz

from pyrogram.enums import ParseMode

logger = LOGGER("cmnd_py")


ERROR_MSG = None
download_msg = status_msg = upload_msg = None



# testing command 
@Bot.on_message(filters.command("gethumb") & filters.private & filters.user(OWNER_ID))
async def get_thumb(client, message):
  if os.path.exists("/app/thumb.jpg"):
    await message.reply_photo(
        photo="/app/thumb.jpg",
        caption="He is the thumb",
    )
  else:
    await message.reply_text("Seems like there is no thumb right there lil bro")



# post command 
@Bot.on_message(filters.command(["post", "POST"]) & filters.private & filters.user(OWNER_ID))
async def post_command(client, message):
  global ERROR_MSG
  
  try:
    if ERROR_MSG:
      try:
        await ERROR_MSG.delete()
      except:
        pass
      ERROR_MSG = None
  
    link = message.text.split() 
    if len(link) <= 1:
      ERROR_MSG = await message.reply_text(
      "No Link Detected! /POST [DIRECT LINK]",
      quote=True
      )
      return 


    try:
        await message.delete() # delete my input msg
    except:
        pass



    # Set Bangladesh timezone
    bd_timezone = pytz.timezone('Asia/Dhaka')
    now = datetime.now(bd_timezone)
    timestamp = now.strftime("%Y-%m-%d %I:%M:%S %p")  # 12-hour format with AM/PM



    d_link = link[1]
    user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    


    log_text = (
        f"> 🕊️ **New Upload Found!**\n\n"
        f"At 🕒 Time:{timestamp}\n"
        f"By {user} (ID: `{message.from_user.id}`)\n"
        f"Link: [LINK 🖇️]({d_link})"
    )

    try:
        await client.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=log_text,
            disable_web_page_preview=True,
            disable_notification=True, # silent msg send no notification
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        pass
 

    filename = f"HENTAIBILI - [{gen_filename()}]"



    # download logic
    download_msg = await message.reply_text("📩 Download Initializing...")
    success, result = await download(d_link, filename, download_msg)
    if not success:
      await message.reply_text(f"Download Failed! {result}")
      return
    
    
    # thumbnail generation 
    status_msg = await message.reply_text("🖼️ Generating Thumbnail!")
    thumbnail_path = await generate_video_thumbnail(result)
    
    if thumbnail_path:
      await status_msg.edit("✅ Thumbnail Generated!")
    else:
      await status_msg.edit("❌ Thumbnail Generation Failed!")
      thumbnail_path = "Assist/default_thumb.jpg"
      logger.error(f"thumbnail_path = {thumbnail_path}")
    
    #Upload logic
    upload_msg = await message.reply_text("📤 Upload Initializing...")
    success, db_msg = await upload(client, result, upload_msg)
    if not success:
      await message.reply_text(f"Upload Failed! {db_msg}")
      return


    # backup file to log channel 
    try:
        await client.copy_message(
            chat_id=LOG_CHANNEL_ID,
            from_chat_id=db_msg.chat.id,
            message_id=db_msg.id
        )
    except Exception as e:
        logger.error(f"Failed to create a backup {e}")


    
    # link generation logic
    share_link, buttons = await link_gen(db_msg)
    if share_link:
      await message.reply_text(f"LINK = {buttons}")
    else:
      await message.reply_text(f"Failed Link Generation!")
      return
    
    # here post name logic
    
   
    if thumbnail_path and os.path.exists(thumbnail_path):
      await message.reply_text(f"THUMB PATH: {thumbnail_path}")
    else:
      await message.reply_text("Thumbnail Path Does not exist")
        
   
    # here main channel post logic 
    try:
        
        if not thumbnail_path or os.path.exists("/app/thumb.jpg"):
          logger.error("Thumbnail not found at /app/thumb.jpg")
          raise FileNotFoundError("Thumbnail not found")


        await client.send_photo(
            chat_id=POST_CHANNEL_ID,
            photo=thumbnail_path,
            caption=None,
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN
        ) 
        
    except Exception as e:
        await message.reply_text(f"Send Post Failed! {str(e)}")
   
   
    f'''#cleanups 
    try:
      if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
        logger.error(f"thumbnail removed {thumbnail_path}")
      if os.path.exists(result):
        os.remove(result)
        logger.error(f"Video removed {result}")
    except Exception as e:
      await message.reply_text(f"Cleanup Failed! {e}")'''
    
   
  except Exception as e:
    await message.reply_text(f"Main Error! {str(e)}")

    
    # clean up pm indicator msgs
  finally:
    for msg in [download_msg, status_msg, upload_msg]:
      if msg:
        try:
            await msg.delete()
        except:
            pass
   

# generate random id for filename
def gen_filename(length=6):
  chars = string.ascii_uppercase + string.digits # A-Z and 0-9
  return ''.join(random.choices(chars, k=length))