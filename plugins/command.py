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
import traceback 
import asyncio 

from pyrogram.enums import ParseMode

logger = LOGGER("cmnd_py")


ERROR_MSG = None
NO_THUMB = "Assist/default_thumb_1.jpg"
download_msg = status_msg = upload_msg = None

# Queue System 
POST_QUEUE = asyncio.Queue() 
IS_PROCESSING = False

#-- here is the forward or upload command handler--#

@Bot.on_message(filters.private & filters.user(OWNER_ID) & (filters.command("genpost") | filters.video | filters.document))
async def local_post_command(client, message):
  logger.info("working on it")





#-- Here is the post command handler--#

# post command 
#@Bot.on_message(filters.command(["post", "POST"]) & filters.private & filters.user(OWNER_ID))
@Bot.on_message(filters.command(["post", "POST"]) & filters.private & filters.user(OWNER_ID))
async def post_command(client, message):
    global ERROR_MSG
     
    download_msg = status_msg = upload_msg = None
     
    try:
        if ERROR_MSG:
            try: await ERROR_MSG.delete()
            except: pass
            ERROR_MSG = None

        link = message.text.split()
        if len(link) <= 1:
            ERROR_MSG = await message.reply_text(
                "No Link Detected! /POST [DIRECT LINK]",
                quote=True
            )
            return

        d_link = link[1]
        await process_post_queue(client, message, d_link)  # 🟩 NEW

    except Exception as e:
        await message.reply_text(f"Main Error! {str(e)}")






async def main_process(client, message, d_link):
  global ERROR_MSG, IS_PROCESSING
  
  try:
    if ERROR_MSG:
      try:
        await ERROR_MSG.delete()
      except:
        pass
      ERROR_MSG = None
  
    '''link = message.text.split() 
    if len(link) <= 1:
      ERROR_MSG = await message.reply_text(
      "No Link Detected! /POST [DIRECT LINK]",
      quote=True
      )
      return'''


    try:
        await message.delete() # delete my input msg
    except:
        pass



    # Set Bangladesh timezone
    bd_timezone = pytz.timezone('Asia/Dhaka')
    now = datetime.now(bd_timezone)
    timestamp = now.strftime("%Y-%m-%d %I:%M:%S %p")  # 12-hour format with AM/PM



    #d_link = link[1]
    #user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    


    '''log_text = (
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
        pass'''
 


    file_id = gen_filename()
    filename = f"HENTAIBILI - [{file_id}]"



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
    buttons = await link_gen(db_msg)
    if buttons:
      logger.info(f"Link GENERATED!")
    else:
      await message.reply_text(f"Failed Link Generation!")
      return
    
    # here post name logic
    
   
    if thumbnail_path and os.path.exists(thumbnail_path):
      logger.info(f"THUMB PATH: {thumbnail_path}")
    else:
      await message.reply_text("Thumbnail Path Does not exist")
        
   
    # here main channel post logic 
    try:
        
        if not thumbnail_path or not os.path.exists(thumbnail_path):
          logger.error("Thumbnail not found at thumbnail_path")
          thumbnail_path = NO_THUMB


        await client.send_photo(
            chat_id=POST_CHANNEL_ID,
            photo=thumbnail_path,
            caption=None,
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN
        ) 
        
    except Exception as e:
        error_text = f"Upload Failed / In POST SECTION!"
        await message.reply_text(f"Send Post Failed! {str(e)}")
        logger.error(error_text)
        logger.error(traceback.format_exc())
   
   
    #cleanups 
    try:
      if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
        logger.error(f"thumbnail removed {thumbnail_path}")
      if os.path.exists(result):
        os.remove(result)
        logger.error(f"Video removed {result}")
    except Exception as e:
      await message.reply_text(f"Cleanup Failed! {e}")
    
   
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

   
# Queue system 
async def process_post_queue(client, message, d_link):
    global IS_PROCESSING
    queue_msg = None
    proc_msg = None




    if IS_PROCESSING:   # already working on another task
        queue_msg = await message.reply_text(f"✅ Added to queue! Position: {POST_QUEUE.qsize()}")
        await POST_QUEUE.put((client, message, d_link, queue_msg))
        return

    IS_PROCESSING = True
    proc_msg = await message.reply_text("🚀 Processing your task now...")

    try:
        # 🔵 run your existing post logic
        await main_process(client, message, d_link)
    finally:
        IS_PROCESSING = False
        # delete processing messages safely
        for msg in [proc_msg, queue_msg]:
            if msg:
                try:
                    await msg.delete()
                except:
                    pass

        # check queue
        if not POST_QUEUE.empty():
            next_item = await POST_QUEUE.get()
            if len(next_item) == 4:
                next_client, next_message, next_link, next_queue_msg = next_item 
        else:
            next_client, next_message, next_link = next_item
            next_queue_msg = None


        if next_queue_msg:
            try:
                await next_queue_msg.delete() 
            except:
                pass
        
        await process_post_queue(next_client, next_message, next_link)
        




# generate random id for filename
def gen_filename(length=6):
  chars = string.ascii_uppercase + string.digits # A-Z and 0-9
  return ''.join(random.choices(chars, k=length))
