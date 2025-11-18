import os
import random
import string
import time
from datetime import datetime
import pytz
import traceback
import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from bot import Bot
from config import OWNER_ID, DOWNLOAD_DIR, CREDIT, DB_CHANNEL_ID, POST_CHANNEL_ID, LOG_CHANNEL_ID, LOGGER, NO_THUMB
from plugins.download import download
from plugins.upload import upload
from plugins.link_gen import link_gen
from plugins.ffmpeg_thumb import generate_video_thumbnail

logger = LOGGER("cmnd_py")

# Global vars
ERROR_MSG = None
POST_QUEUE = asyncio.Queue()
IS_PROCESSING = False

#----------------------------#
# Command to generate post
#----------------------------#
@Bot.on_message(filters.private & filters.user(OWNER_ID) & (filters.command("genpost") | filters.video | filters.document))
async def local_post_command(client, message):
    logger.info("Working on it...")

#----------------------------#
# Post command handler
#----------------------------#
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

        args = message.text.split()
        if len(args) <= 1:
            ERROR_MSG = await message.reply_text(
                "No Link Detected! /POST [DIRECT LINK]",
                quote=True
            )
            return

        d_link = args[1]
        await process_post_queue(client, message, d_link)

    except Exception as e:
        await message.reply_text(f"Main Error! {str(e)}")

#----------------------------#
# Main processing logic
#----------------------------#
async def main_process(client, message, d_link):
    download_msg = status_msg = upload_msg = None
    try:
        if ERROR_MSG:
            try:
                await ERROR_MSG.delete()
            except:
                pass

        # Delete user's input message
        try:
            await message.delete()
        except:
            pass

        # Timestamp
        bd_timezone = pytz.timezone('Asia/Dhaka')
        now = datetime.now(bd_timezone)
        timestamp = now.strftime("%Y-%m-%d %I:%M:%S %p")

        # Generate filenames
        file_id = gen_filename()
        filename = f"HENTAIBILI - [{file_id}]"

        # Download
        download_msg = await message.reply_text("📩 Download Initializing...")
        success, result = await download(d_link, filename, download_msg)
        if not success:
            await message.reply_text(f"Download Failed! {result}")
            return

        # Thumbnail generation
        status_msg = await message.reply_text("🖼️ Generating Thumbnail!")
        thumbnail_path = await generate_video_thumbnail(result)
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
            return

        # Backup in log channel
        try:
            await client.copy_message(
                chat_id=LOG_CHANNEL_ID,
                from_chat_id=db_msg.chat.id,
                message_id=db_msg.id
            )
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

        # Link generation
        buttons = await link_gen(db_msg)
        if buttons:
            logger.info("Link GENERATED!")
        else:
            await message.reply_text("Failed Link Generation!")
            return

        # Post to main channel
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            logger.error("Thumbnail not found, using default.")
            thumbnail_path = NO_THUMB

        await client.send_photo(
            chat_id=POST_CHANNEL_ID,
            photo=thumbnail_path,
            caption=None,
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(traceback.format_exc())
        await message.reply_text(f"Error in processing post: {str(e)}")

    finally:
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

#----------------------------#
# Queue processing system
#----------------------------#
async def process_post_queue(client, message, d_link):
    global IS_PROCESSING
    queue_msg = None
    proc_msg = None

    # Already processing
    if IS_PROCESSING:
        queue_msg = await message.reply_text(f"✅ Added to queue! Position: {POST_QUEUE.qsize() + 1}")
        await POST_QUEUE.put((client, message, d_link, queue_msg))
        return

    # Mark as processing
    IS_PROCESSING = True
    proc_msg = await message.reply_text("🚀 Processing your task now...")

    try:
        await main_process(client, message, d_link)
    finally:
        IS_PROCESSING = False

        # Delete processing messages safely
        for msg in [proc_msg, queue_msg]:
            if msg:
                try:
                    await msg.delete()
                except:
                    pass

        # Process next item in queue
        if not POST_QUEUE.empty():
            next_item = await POST_QUEUE.get()
            # Safe unpacking
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

#----------------------------#
# Generate random filename
#----------------------------#
def gen_filename(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))