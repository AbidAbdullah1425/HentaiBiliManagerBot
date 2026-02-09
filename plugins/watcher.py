import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import LOGGER, POST_CHANNEL_ID, OWNER_ID, CNL_BUTTON_NAME
from database.database import get_oldest_post, delete_post

logger = LOGGER(__name__)


@Client.on_message(filters.user(OWNER_ID) & filters.private & filters.command("start_watcher"))
async def start_watcher_manually_cmd(client, message):
    if getattr(client, "watcher_task", None) and not client.watcher_task.done():
        await message.reply_text("Watcher already running")
        return

    client.watcher_task = asyncio.create_task(watcher_loop(client))
    await message.reply_text("Watcher started")


@Client.on_message(filters.user(OWNER_ID) & filters.private & filters.command("stop_watcher"))
async def stop_watcher_manually_cmd(client, message):
    task = getattr(client, "watcher_task", None)

    if not task or task.done():
        await message.reply_text("Watcher not running")
        return

    task.cancel()
    await message.reply_text("Watcher stopping...")


async def watcher_loop(client):
    try:
        while True:
            post = await get_oldest_post()
            if not post:
                await client.send_message(OWNER_ID, "No pending posts. Watcher stopped.")
                break

            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(CNL_BUTTON_NAME, url=post["start_link"])]
            ])

            await client.send_photo(
                chat_id=POST_CHANNEL_ID,
                photo=post["cover"],
                caption=post["caption"],
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
                has_spoiler=True
            )

            await delete_post(post["_id"])
            await asyncio.sleep(client.watcher_time * 3600)

    except asyncio.CancelledError:
        logger.info("Watcher cancelled")
        raise
