import asyncio
import os

import aiofiles
import aiohttp
import filetype

from config import DOWNLOAD_DIR, LOGGER
from plugins.progressbar import TelegramProgressReporter, TransferState

logger = LOGGER("download_py")

PROGRESS_UPDATE_INTERVAL = 3.0
CHUNK_SIZE = 1024 * 1024


async def download_thumb(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()

    save_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
    async with aiofiles.open(save_path, "wb") as file_obj:
        await file_obj.write(data)

    return save_path


async def _download(url, filename, message):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    state = TransferState(status="DOWNLOADING...")
    reporter = TelegramProgressReporter(
        message=message,
        state=state,
        update_interval=PROGRESS_UPDATE_INTERVAL,
    )
    reporter_task = None

    try:
        timeout = aiohttp.ClientTimeout(
            total=None,
            sock_connect=30,
            sock_read=300,
        )

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return False, f"Expired or Invalid URL {response.status}"

                total_header = response.headers.get("Content-Length")
                total = int(total_header) if total_header and total_header.isdigit() else None
                if total and total > 0:
                    state.total = total

                reporter_task = asyncio.create_task(reporter.run())

                downloaded = 0
                with open(filepath, "wb", buffering=CHUNK_SIZE) as file_obj:
                    async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                        if not chunk:
                            continue
                        file_obj.write(chunk)
                        downloaded += len(chunk)
                        state.set_progress(downloaded, total)

        if os.path.getsize(filepath) < 100 * 1024:
            os.remove(filepath)
            state.mark_failed("Download failed: file too small (invalid video)")
            return False, "Download failed: file too small (invalid video)"

        kind = filetype.guess(filepath)
        ext = "." + kind.extension if kind else ""

        if ext and not filename.endswith(ext):
            new_path = filepath + ext
            os.rename(filepath, new_path)
            filepath = new_path
            logger.info("FileName: %s | FilePath: %s", new_name, filepath)

        state.mark_done()
        if reporter_task is not None:
            reporter.stop()
            await reporter_task
        await message.edit_text("Download Completed")
        return True, filepath

    except Exception as exc:
        state.mark_failed(str(exc))
        if reporter_task is not None:
            try:
                reporter.stop()
                await reporter_task
            except Exception:
                pass
        return False, str(exc)


async def download(url, filename, message):
    return await _download(url, filename, message)
