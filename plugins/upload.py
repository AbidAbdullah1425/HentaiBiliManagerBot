import asyncio
import os

from pyrogram import Client
from pyrogram.enums import ParseMode

from config import CREDIT, DB_CHANNEL_ID
from plugins.progressbar import TelegramProgressReporter, TransferState

PROGRESS_UPDATE_INTERVAL = 3.0


async def upload(bot: Client, filepath, message):
    state = TransferState(status="UPLOADING...")
    reporter = TelegramProgressReporter(
        message=message,
        state=state,
        update_interval=PROGRESS_UPDATE_INTERVAL,
    )
    reporter_task = None

    try:
        if not os.path.exists(filepath):
            await message.reply_text(f"File NOT found! {filepath}")
            raise FileNotFoundError(f"File NOT Found {filepath}")

        reporter_task = asyncio.create_task(reporter.run())

        async def prog(current, total):
            state.set_progress(current=current, total=total)

        send_vid = await bot.send_video(
            chat_id=DB_CHANNEL_ID,
            video=filepath,
            caption=CREDIT,
            parse_mode=ParseMode.HTML,
            progress=prog,
        )

        state.mark_done()
        if reporter_task is not None:
            reporter.stop()
            await reporter_task

        await message.edit_text("Upload Completed")
        return True, send_vid

    except Exception as exc:
        state.mark_failed(str(exc))
        if reporter_task is not None:
            try:
                reporter.stop()
                await reporter_task
            except Exception:
                pass
        return False, str(exc)
