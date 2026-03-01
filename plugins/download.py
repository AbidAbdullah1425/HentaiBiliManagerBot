import asyncio
import time
import filetype
import os
import aiohttp
import aiofiles
from config import DB_CHANNEL_ID, POST_CHANNEL_ID, DOWNLOAD_DIR, CREDIT, LOGGER
from plugins.progressbar import progress_bar

logger = LOGGER("download_py")


async def download_thumb(url):
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.read()

    save_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(data)

    return save_path


async def _download(url, filename, message):
    try:
        status = "DOWNLOADING..."
        start = time.time()
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        timeout = aiohttp.ClientTimeout(
            total=None,
            sock_connect=30,
            sock_read=180
        )

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:

                if resp.status != 200:
                    return False, f"Expired or Invalid URL {resp.status}"

                total = int(resp.headers.get("Content-Length", 0))
                if total == 0:
                    return False, "Content Length = 0"

                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                last_update = 0

                async with aiofiles.open(filepath, "wb") as f:
                    async for chunk in resp.content.iter_chunked(chunk_size):

                        if not chunk:
                            continue

                        await f.write(chunk)
                        downloaded += len(chunk)

                        # update progress every 2 seconds only
                        now = time.time()
                        if now - last_update > 2:
                            await progress_bar(
                                current=downloaded,
                                total=total,
                                start_time=start,
                                status=status,
                                message=message
                            )
                            last_update = now

        # validate file size
        if os.path.getsize(filepath) < 100 * 1024:
            os.remove(filepath)
            return False, "Download failed: file too small"

        # detect extension
        kind = filetype.guess(filepath)
        ext = "." + kind.extension if kind else ""

        if ext and not filename.endswith(ext):
            new_path = filepath + ext
            os.rename(filepath, new_path)
            filepath = new_path

        return True, filepath

    except Exception as e:
        return False, str(e)


# Wrapper
async def download(url, filename, message):
    return await _download(url, filename, message)