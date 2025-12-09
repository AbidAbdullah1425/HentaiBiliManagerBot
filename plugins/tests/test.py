import aiohttp
import asyncio
import os
import time
from pyrogram import Client, filters
from bot import Bot
from config import LOGGER, OWNER_ID
from plugins.progressbar import progress_bar  # your existing progress bar

log = LOGGER("GG")

# Hardcoded URLs
LINKS = {
    "gogo": "https://rr2---sn-vg5obxgv-vu2s.googlevideo.com/videoplayback?expire=1765319656&ei=aDM4aeDuLp3AkucPl5eYoQ0&ip=86.62.59.234&id=38612b7f8b8dfa66&itag=18&source=blogger&xpc=Egho7Zf3LnoBAQ%3D%3D&met=1765290856,&mh=Xh&mm=31&mn=sn-vg5obxgv-vu2s&ms=au&mv=m&mvi=2&pl=23&rms=au,au&susc=bl&eaua=rtoJOzg_lbM&mime=video/mp4&vprv=1&rqh=1&dur=1415.906&lmt=1765133445193770&mt=1765290552&txp=1311224&sparams=expire,ei,ip,id,itag,source,xpc,susc,eaua,mime,vprv,rqh,dur,lmt&sig=AJfQdSswRAIgQPvf3efRPQe1ZT4ENKUwv6ttqmEcJ5j7pbFHdxb-cI4CIDhKyXvxjmMS3FpMMr3AZIVePKxOs0080-WKn39NYx52&lsparams=met,mh,mm,mn,ms,mv,mvi,pl,rms&lsig=APaTxxMwRQIgMVfGaHk8S_qOIK-8gtBQHqGQ7oPAcLJ7dm2IdgDIXAwCIQC13IhQ66iNzUZu2gzLQubgAKMc0saI8e7_Z2Zv4Fupvw%3D%3D",
    "animepahe": "https://vault-99.owocdn.top/stream/99/01/15b745f84e01146ba1632b4b2366f6ba5bbe0ea051583ac0e42e669c98169477/uwu.m3u8"
}

async def download_file(session, url, filename, message):
    """Async download with progress bar and logging"""
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                msg = f"HTTP error {resp.status} | Headers: {resp.headers}"
                log.error(msg)
                return msg

            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()

            with open(filename, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        await progress_bar(downloaded, total, start_time, message, "Downloading")

            msg = f"Download finished: {filename}"
            log.info(msg)
            return msg

    except Exception as e:
        msg = f"Download failed: {e}"
        log.error(msg)
        return msg

@Bot.on_message(filters.command("testdl") & filters.private & filters.user(OWNER_ID))
async def test_download(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /testdl <gogo|animepahe>")
        return

    choice = message.command[1].lower()
    if choice not in LINKS:
        msg = "Invalid choice. Use gogo or animepahe."
        log.error(msg)
        await message.reply_text(msg)
        return

    url = LINKS[choice]
    filename = f"{choice}_test.mp4" if choice == "gogo" else f"{choice}_test.m3u8"
    status_msg = await message.reply_text(f"Starting download for {choice}...")

    async with aiohttp.ClientSession() as session:
        result = await download_file(session, url, filename, status_msg)

    await status_msg.edit_text(f"Result: {result}")

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)