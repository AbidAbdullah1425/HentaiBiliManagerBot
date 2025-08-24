import base64
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_USERNAME


async def encode(text: str) -> str:
  return base64.urlsafe_b64encode(text.encode()).decode


async def link_gen(Bot: Client, message, db_channel, up_msg_id_status):
  encoded = encode(f"get-{up_msg_id_status * abs(db_channel)}")
  start_link = f"https://t.me/{BOT_USERNAME}?start={encoded}"
  
  buttons = InlineKeyboardMarkup([[InlineKeyboardButton("📺 Watch / Download", url=start_link)]])
  
  return buttons