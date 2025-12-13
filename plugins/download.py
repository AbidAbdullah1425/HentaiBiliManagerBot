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
            sock_read=70,
            sock_connect=70
        )

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:

                # URL invalid / expired
                if resp.status != 200:
                    return False, f"Expired or Invalid URL {resp.status}"

                # No length = dead/expired URL
                total = int(resp.headers.get("Content-Length", 0))
                if total == 0:
                    return False, "Content Length = 0"

                downloaded = 0
                last_data = time.time()

                # Start writing file
                with open(filepath, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 256):

                        if not chunk:
                            if time.time() - last_data > 180:
                                return False, "Download Stalled! (no data)."
                            await asyncio.sleep(0.3)
                            continue

                        f.write(chunk)
                        downloaded += len(chunk)
                        last_data = time.time()

                        # Progress bar
                        await progress_bar(
                            current=downloaded,
                            total=total,
                            start_time=start,
                            status=status,
                            message=message
                        )

                await message.edit("🌆 Download Completed")

        # If video too small = invalid or broken
        if os.path.getsize(filepath) < 100 * 1024:
            os.remove(filepath)
            return False, "Download failed: file too small (invalid video)"

        # Detect extension
        kind = filetype.guess(filepath)
        ext = "." + kind.extension if kind else ".mp4"

        # Rename file if extension missing
        if ext and not filename.endswith(ext):
            new_name = filename + ext
            new_path = os.path.join(DOWNLOAD_DIR, new_name)
            os.rename(filepath, new_path)
            filepath = new_path
            logger.error(f"FileName: {new_name}\nFilePath: {filepath}")

        return True, filepath

    except Exception as e:
        return False, str(e)


# Wrapper
async def download(url, filename, message):
    return await _download(url, filename, message)