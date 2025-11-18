import os, shutil 
import gc
import random
import string
import time
from datetime import datetime
import pytz
import traceback
import asyncio
import logging
from urllib.parse import urlparse
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
import json
from bot import Bot
from config import OWNER_ID, DOWNLOAD_DIR, CREDIT, DB_CHANNEL_ID, POST_CHANNEL_ID, LOG_CHANNEL_ID, LOGGER, NO_THUMB
from plugins.download import download, download_thumb
from plugins.upload import upload
from plugins.link_gen import link_gen
from plugins.ffmpeg_thumb import generate_video_thumbnail

logger = LOGGER("join_release.py")

@Bot.on_message(
    filters.user(OWNER_IDS) &
    (filters.video | (filters.document & filters.create(lambda _, __, m: m.document and (m.document.file_name.endswith(".json"))))
)
async json_release(client: Client, message: Message):
    # Default Values
    thumbnail_path = None
    result = None
    download_msg = None
    status_msg = None
    upload_msg = None

    try:
        # Read json 
        filepath = await message.download() 
    
        with open(filepath) as f:
            data = json.load(f) 
    
        GLOBAL_DATA = []
        for item in data:
            GLOBAL_DATA.append({
                "url": item["url"],
                "studio": item["studio"],
                "genres": item["genres"],
                "cover": item["cover"],
                "preview_images_urls": item["preview_images_urls"],
                "video_url": item["video_url"]
            })
        for item in GLOBAL_DATA:
            url = item["url"]
            studio = item["studio"]
            genres = item["genres"]
            cover = item["cover"]
            preview_images_urls = item["preview_images_urls"]
            video_url = item["video_url"]
            
            title = extract_title(url) # title of the media
         
            # Download
            download_msg = await message.reply_text("📩 Download Initializing...")
            success, result = await download(video_url, title, download_msg)
            if not success:
                await message.reply_text(f"Download Failed! {result}")
                continue
    
            # Thumbnail Download 
            status_msg = await message.reply_text("🖼️ Downloading Thumbnail!")
            thumbnail_path = await download_thumb(cover) 
            if thumbnail_path:
                await status_msg.edit("✅ Thumbnail Generated!")
            else:
                await status_msg.edit("❌ Thumbnail Generation Failed!")
                thumbnail_path = NO_THUMB
                logger.error(f"thumbnail_path = {thumbnail_path}")
        
            # Upload
            upload_msg = await message.reply_text("📤 Upload Initializing...")
            success, db_msg = await upload(client, result, upload_msg)
            if not success:
                await message.reply_text(f"Upload Failed! {db_msg}")
                continue
        
            # Link generation
            buttons = await link_gen(db_msg)
            if buttons:
                logger.info("Link GENERATED!")
            else:
                await message.reply_text("Failed Link Generation!")
                continue
        
            # Post to main channel
            if not thumbnail_path or not os.path.exists(thumbnail_path):
                logger.error("Thumbnail not found, using default.")
                thumbnail_path = NO_THUMB
           
            caption = (
                f"<blockquote>{title}</blockquote>\n\n"
                f"<blockquote>• Studio: {studio}</blockquote>\n"
                f"<blockquote>• Genres: {genres}</blockquote>\n"
                f"<blockquote><a href='https://t.me/+O7PeEMZOAoMzYzVl'>⌘ ʜᴇɴᴛᴀɪᴄɪsᴘ</a></blockquote>"
            )
            
            await client.send_photo(
                chat_id=POST_CHANNEL_ID,
                photo=thumbnail_path,
                caption=caption,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
            
            # Cleanup
            for path in [thumbnail_path, result]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                        logger.info(f"Removed file: {path}")
                    except Exception as e:
                        logger.error(f"Failed cleanup {path}: {e}")

            for msg in [download_msg, status_msg, upload_msg]:
                    if msg:
                        try:
                            await msg.delete()
                        except:
                            pass
        
    except Exception as e:
        logger.error(traceback.format_exc())
        await message.reply_text(f"Error in processing post: {str(e)}")

    finally:
        if os.path.exists(DOWNLOAD_DIR):
            shutil.rmtree(DOWNLOAD_DIR)
            os.makedirs(DOWNLOAD_DIR)
        
        
        gc.collect()


def extract_title(url: str) -> str:
    path = urlparse(url).path.rstrip("/") 
    slug = path.split("/")[-1] 
    
    words = slug.split("-") 
    words = [w.capitalize() for w in words] 
    
    title = " ".join(words) 
    
    return title