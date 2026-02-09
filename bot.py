from aiohttp import web
from plugins import web_server
import asyncio
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
from plugins.watcher import watcher_loop 
import sys
from datetime import datetime
import pyrogram.utils
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, DB_CHANNEL_ID, PORT

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER 
        self.watcher_time = 6
        self.watcher_task = None

    async def start(self):
        await super().start() 
        user_info = await self.get_me()
        self.LOGGER(__name__).info(f"Bot: @{user_info.username}")
        self.uptime = datetime.now()
        try:
            db_channel = await self.get_chat(DB_CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Make sure the bot is an Admin in the DB Channel, and double-check the CHANNEL_ID value. Current value: {DB_CHANNEL_ID}")
            self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/weebs_support or CodexBot for support")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/codeflix_bots")
        # Start the watcher task
        self.LOGGER(__name__).info("Starting watcher task...")
        asyncio.create_task(watcher_loop(self))
        self.LOGGER(__name__).info(f"""       
  ___ ___  ___  ___ ___ _    _____  _____  ___ _____ ___ 
 / __/ _ \|   \| __| __| |  |_ _\ \/ / _ )/ _ \_   _/ __|
| (_| (_) | |) | _|| _|| |__ | | >  <| _ \ (_) || | \__ \
 \___\___/|___/|___|_| |____|___/_/\_\___/\___/ |_| |___/
                                                         
 
                                          """)


        # web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")
