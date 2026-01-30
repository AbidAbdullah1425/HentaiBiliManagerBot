from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from database.database import get_oldest_post, delete_post, get_all_posts
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, POST_CHANNEL_ID, CNL_BUTTON_NAME

@Client.on_message(filters.user(OWNER_ID) & filters.command("m_post"))
async def manual_post(client, message):
    """Manually send the oldest post in DB"""
    post = await get_oldest_post()
    if not post:
        await message.reply_text("No pending posts in the queue.")
        return
    
    markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(CNL_BUTTON_NAME, url=post.get("start_link"))
                    ]
                ]
            )

    try:
        await client.send_photo(
            chat_id=POST_CHANNEL_ID,
            photo=post["cover"],
            caption=post["caption"],
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            has_spoiler=True
        )
        await delete_post(post["_id"])
        await message.reply_text("✅ Post sent manually and removed from queue.")
    except Exception as e:
        await message.reply_text(f"Failed to send post: {e}")



# List all waiting posts by title
@Client.on_message(filters.user(OWNER_ID) & filters.command("list_posts"))
async def list_posts(client, message):
    posts = await get_all_posts()
    if not posts:
        await message.reply_text("No pending posts in the queue.")
        return

    text = "📋 **Pending Posts Titles:**\n\n"
    for i, post in enumerate(posts, 1):
        title = post.get("title", "Untitled")
        text += f"{i}. {title}\n"

    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)