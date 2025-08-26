from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "about":
        await query.message.edit_text(
            text=(
                "<b>○ Oᴡɴᴇʀ:</b> <a href='tg://user?id={OWNER_ID}'>@OnlyNoco</a>\n"
                "<b>○ Mᴀɪɴ Cʜᴀɴɴᴇʟ:</b> <a href='https://t.me/HeavenlySubs'>HᴇᴀᴠᴇɴʟʏSᴜʙs</a>\n"
                "<b>○ Wᴇʙsɪᴛᴇ:</b> <a href='https://onlynoco.vercel.app'>Pᴏʀᴛғᴏʟɪᴏ</a>\n"
                "<b>○ Dᴏɴᴀᴛᴇ:</b> <a href='https://onlynoco.vercel.app/donate'>Sᴜᴘᴘᴏʀᴛ</a>"
            ).format(OWNER_ID=OWNER_ID),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔒 Close", callback_data="close")]]
            )
        )
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass