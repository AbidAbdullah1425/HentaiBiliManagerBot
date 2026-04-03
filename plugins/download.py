import asyncio
import os

import aiofiles
import aiohttp
import filetype

from config import DOWNLOAD_DIR, LOGGER
from plugins.progressbar import TelegramProgressReporter, TransferState

logger = LOGGER("download_py")

PROGRESS_UPDATE_INTERVAL = float(os.environ.get("PROGRESS_UPDATE_INTERVAL", "8"))
CHUNK_SIZE = 1024 * 1024
# CHANGE: Minimum size guard to prevent saving expired/HTML/error payloads.
MIN_VALID_CONTENT_LENGTH = int(os.environ.get("MIN_VALID_DOWNLOAD_BYTES", str(100 * 1024)))  # default 100KB
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


async def download_thumb(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()

    save_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
    async with aiofiles.open(save_path, "wb") as file_obj:
        await file_obj.write(data)

    return save_path


def _validate_download_response(response: aiohttp.ClientResponse) -> int | None:
    # CHANGE: Validate response BEFORE writing anything to disk.
    if response.status != 200:
        raise RuntimeError(f"Expired or Invalid URL {response.status}")

    content_type = (response.headers.get("Content-Type") or "").lower()
    # CHANGE: Many CDNs send videos as application/octet-stream.
    if ("video" not in content_type) and ("application/octet-stream" not in content_type):
        raise RuntimeError(f"Invalid Content-Type: {response.headers.get('Content-Type')}")

    content_length_header = response.headers.get("Content-Length")
    try:
        content_length = int(content_length_header) if content_length_header else 0
    except ValueError:
        content_length = 0

    # CHANGE: If Content-Length is present, enforce minimum; if missing, allow but rely on post-download check.
    if content_length and content_length <= MIN_VALID_CONTENT_LENGTH:
        raise RuntimeError(
            f"Invalid Content-Length: {content_length_header} (must be > {MIN_VALID_CONTENT_LENGTH})"
        )

    return content_length if content_length > 0 else None


async def _download_once(url, filename, message, state: TransferState, referer=None):
    # CHANGE: Write to a temporary ".part" file; rename only after validation.
    basepath = os.path.join(DOWNLOAD_DIR, filename)
    partpath = basepath + ".part"
    final_path = None
    reporter_task = None

    try:
        timeout = aiohttp.ClientTimeout(
            total=None,
            sock_connect=30,
            sock_read=300,
        )

        headers = dict(DEFAULT_REQUEST_HEADERS)
        if referer:
            headers["Referer"] = referer

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                total = _validate_download_response(response)
                state.total = total

                # CHANGE: Progress reporter starts after we validated the response.
                reporter = TelegramProgressReporter(
                    message=message,
                    state=state,
                    update_interval=PROGRESS_UPDATE_INTERVAL,
                )
                reporter_task = asyncio.create_task(reporter.run())

                downloaded = 0
                # Ensure old partial isn't reused.
                try:
                    if os.path.exists(partpath):
                        os.remove(partpath)
                except Exception:
                    pass

                with open(partpath, "wb", buffering=CHUNK_SIZE) as file_obj:
                    async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                        if not chunk:
                            continue
                        file_obj.write(chunk)
                        downloaded += len(chunk)
                        state.set_progress(downloaded, total)

        # CHANGE: Post-download guard. Content-Length can lie; keep the local check too.
        if os.path.getsize(partpath) < MIN_VALID_CONTENT_LENGTH:
            try:
                os.remove(partpath)
            except Exception:
                pass
            raise RuntimeError("Download failed: file too small (invalid video)")

        kind = filetype.guess(partpath)
        ext = "." + kind.extension if kind else ".mp4"

        final_path = basepath if (ext and filename.endswith(ext)) else (basepath + ext)
        os.replace(partpath, final_path)
        logger.info("FileName: %s | FilePath: %s", os.path.basename(final_path), final_path)

        if reporter_task is not None:
            reporter.stop()
            await reporter_task
        return final_path

    except Exception as exc:
        # CHANGE: Ensure we never leave partial files behind.
        try:
            for path in (partpath, final_path):
                if path and os.path.exists(path):
                    os.remove(path)
        except Exception:
            pass

        if reporter_task is not None:
            try:
                reporter.stop()
                await reporter_task
            except Exception:
                pass
        raise


async def download(url, filename, message, referer=None):
    """
    CHANGE:
    - Validates response headers BEFORE writing to disk:
        - status == 200
        - "video" in Content-Type
        - Content-Length > 100KB
    """
    state = TransferState(status="DOWNLOADING...")

    try:
        state.status = "DOWNLOADING..."
        state.set_progress(0, None)

        logger.info("Start download: %s", filename)
        final_path = await _download_once(url, filename, message, state, referer=referer)
        state.mark_done()
        await message.edit_text("Download Completed")
        logger.info("Download success: %s", final_path)
        return True, final_path

    except Exception as exc:
        logger.error("Download failed: %s | %s", filename, str(exc))
        state.mark_failed(str(exc))
        return False, str(exc)
