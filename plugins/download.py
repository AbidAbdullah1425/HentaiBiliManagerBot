import asyncio
import time
import filetype
import os
import aiohttp
from config import DB_CHANNEL_ID, POST_CHANNEL_ID, DOWNLOAD_DIR, CREDIT
from plugins.progressbar import progress_bar

async def _download(url, filename, message):
  try:
    status = "DOWNLOADING..."
    start = time.time()
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(filepath, "wb") as f:

          
          status_msg = await message.reply_text("📩 Download Initializing...")


          async for chunk in resp.content.iter_chunked(1024 * 256):
              f.write(chunk)
              downloaded += len(chunk) 
            

              # CALL FOR THE PROG BAR
              await progress_bar(
                  current=downloaded,
                  total=total,
                  start_time=start,
                  status=status,
                  message=status_msg
              ) 

          await status_msg.edit("🌆 Download Completed")


    kind = filetype.guess(filepath)
    ext = "." + kind.extension if kind else ".mp4"
  
    if ext and not filename.endswith(ext):
      new_name = filename + ext 
      new_path = os.path.join(DOWNLOAD_DIR, new_name)
      os.rename(filepath, new_path)
      await message.reply_text(f"FileName: {new_name}") 
   
    return True, filepath
  except Exception as e:
    return False, str(e)



# wrap the _download so i can call it from anywhere easily
async def download(url, filename, message):
  return await _download(url, filename, message)