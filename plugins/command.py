import os 
import random
import string
import time
from bot import Bot
from config import OWNER_ID, DOWNLOAD_DIR, CREDIT, DB_CHANNEL_ID
from pyrogram import Client, filters
from plugins.download import download
from plugins.upload import upload
from plugins.link_gen import link_gen
from plugins.ffmpeg_thumb import generate_video_thumbnail


ERROR_MSG = None


# post command 
@Bot.on_message(filters.command("POST") & filters.private & filters.user(OWNER_ID))
async def post_command(Client, message):
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
    ERROR_MSG = message.reply_text(
      "No Link Detected! /POST [DIRECT LINK]",
      quote=True
    )
    return 
  
    d_link = link[1] #direct link
    filename = f"HENTAIBILI - [{gen_filename()}]"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # download logic
    success, result = await download(d_link, filename, message)
    if not success:
      await message.reply_text(f"Download Failed! {result}")
      return
    
    
    # thumbnail generation 
    status_msg = await message.reply_text("🖼️ Generating Thumbnail! ")
    thumbnail_path = await generate_video_thumbnail(filepath)
    
    if thumbnail_path:
      await status_msg.edit("✅ Thumbnail Generated!")
    else:
      await status_msg.edit("❌ Thumbnail Generation Failed!")
      thumbnail_path = Assist/default_thumb.jpg
    
    #Upload logic
    success, db_msg = await upload(filepath, CREDIT, message)
    if not success:
      await message.reply_text(f"Upload Failed! {result}")
      return
    
    # link generation logic
    share_link, buttons = await link_gen(db_msg)
    if not share_link:
      await message.result(f"Failed Link Generation!")
      return
    
    # here post name logic
    
   
   
   
   # here main channel post logic 
    try:
      awsit client.send_photo(
        chat_id=MAIN_CHANNEL_ID,
        photo=thumbnail_path,
        caption=None,
        reply_markup=buttons
      )
    except Exception as e:
      awsit message.reply_text(f"Send Post Failed! {str(e)}")
   
   
   # cleanups 
    try:
      if os.path.exists(thumbnail_path):
      os.remove(thumbnail_path)
      if os.path.exists(result):
      os.remove(result)
    except Exception as e:
      await message.reply_text(f"Cleanup Failed! (e)")
    
   
  except Exception as e:
    await message.reply_text(f"Main Error! {str(e)}")
   

# generate random id for filename
def gen_filename(length=6):
  chars = string.ascii_uppercase + string.digits # A-Z and 0-9
  return ''.join(random.choices(chars, k=length))