import os 
import random
import string
import time
from bot import Bot
from config import OWNER_ID, DOWNLOAD_DIR, CREDIT, DB_CHANNEL_ID
from pyrogram import Client, filters
from plugins.download import download
from plugins.upload import upload

ERROR_MSG = None


# post command 
@Bot.on_message(filters.command("post") & filters.private & filters.user(OWNER_ID))
async def post_command(Client, message):
  global ERROR_MSG
  
  if ERROR_MSG:
    try:
      await ERROR_MSG.delete()
    except:
      pass
  
  link = message.text.split() 
  if len(link) > 1:
    d_link = link[1] #direct link
    filename = f"HENTAIBILI - [{gen_filename()}]"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    try:
      dl_status = await download(d_link, filename, message) #call for download with progbar
    except Exception as e:
      await message.reply_text(f"Download Failed {e}")
    else:
      if dl_status:
        try:
          up_status = await upload(filepath, CREDIT, message) # call for upload 
        except Exception as e:
          await message.reply_text(f"Upload Error {e}")
        else:
          if up_status:
            link_generation = await link_gen(DB_CHANNEL_ID, send_video) # call for the link gen
          else:
            await message.reply_text(f"Upload Failed & Link Gen Stopped!") 
      else:
        await message.reply_text(f"Download Failed & Next Funcs Stopped!")
        
 #    try:
#       dl_status = await download(d_link, filename, message) #call for download with progbar
#       if dl_status:
#         up_status = await upload(filepath, CREDIT, message) # call for upload 
#       else:
#         await message.reply_text()
#       try:
#         if up_status:
#         link_generation = await link_gen(DB_CHANNEL_ID, send_video) # call for the link gen 
#         #here now create the post but first export thumb from the vid
#       except Exception as e:
#         await message.reply_text(f"Upload Error {e}")
#     except Exception as e: 
#       await message.reply_text(f"Download Failed {e}")
#     
#   else:
#     ERROR_MSG = await message.reply_text("No Link Found! Try Again :(", quote=True) 
# 


# generate random id for filename
def gen_filename(length=6):
  chars = string.ascii_uppercase + string.digits # A-Z and 0-9
  return ''.join(random.choices(chars, k=length))