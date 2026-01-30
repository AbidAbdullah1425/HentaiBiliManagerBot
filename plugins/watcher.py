import asyncio
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import LOGGER, POST_CHANNEL_ID, OWNER_ID, CNL_BUTTON_NAME
from database.database import get_oldest_post, delete_post


logger = LOGGER(__name__)


async def watcher_loop(client):
    while True:
        try:
            post = await get_oldest_post()
            if not post:
                await client.send_message(
                    chat_id=OWNER_ID,
                    text="No pending posts in the queue. Watcher stopped."
                )
                logger.info("No pending posts. Watcher stopped.")
                break

            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(CNL_BUTTON_NAME, url=post.get("start_link"))
                    ]
                ]
            )

            # Send post
            await client.send_photo(
                chat_id=POST_CHANNEL_ID,
                photo=post["cover"],
                caption=post["caption"],
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
                has_spoiler=True
            )

            # Remove from DB
            await delete_post(post["_id"])
            # Wait hours
            await asyncio.sleep(client.watcher_time * 3600)

        except Exception as e:
            await client.send_message(
                chat_id=OWNER_ID,
                text=f"Watcher stopped because of exception {e}"
            )
            logger.info(f"No pending posts. Watcher stopped.{e}")
            return
