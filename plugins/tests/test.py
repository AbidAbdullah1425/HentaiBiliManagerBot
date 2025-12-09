from pyrogram import Client, filters
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
import os
from bot import Bot
from config import LOGGER  # your custom LOGGER function

log = LOGGER("GG")

# Hardcoded URLs
LINKS = {
    "gogo": "https://rr2---sn-vg5obxgv-vu2s.googlevideo.com/videoplayback?expire=1765319656&ei=aDM4aeDuLp3AkucPl5eYoQ0&ip=86.62.59.234&id=38612b7f8b8dfa66&itag=18&source=blogger&xpc=Egho7Zf3LnoBAQ%3D%3D&met=1765290856,&mh=Xh&mm=31&mn=sn-vg5obxgv-vu2s&ms=au&mv=m&mvi=2&pl=23&rms=au,au&susc=bl&eaua=rtoJOzg_lbM&mime=video/mp4&vprv=1&rqh=1&dur=1415.906&lmt=1765133445193770&mt=1765290552&txp=1311224&sparams=expire,ei,ip,id,itag,source,xpc,susc,eaua,mime,vprv,rqh,dur,lmt&sig=AJfQdSswRAIgQPvf3efRPQe1ZT4ENKUwv6ttqmEcJ5j7pbFHdxb-cI4CIDhKyXvxjmMS3FpMMr3AZIVePKxOs0080-WKn39NYx52&lsparams=met,mh,mm,mn,ms,mv,mvi,pl,rms&lsig=APaTxxMwRQIgMVfGaHk8S_qOIK-8gtBQHqGQ7oPAcLJ7dm2IdgDIXAwCIQC13IhQ66iNzUZu2gzLQubgAKMc0saI8e7_Z2Zv4Fupvw%3D%3D",
    "animepahe": "https://vault-99.owocdn.top/stream/99/01/15b745f84e01146ba1632b4b2366f6ba5bbe0ea051583ac0e42e669c98169477/uwu.m3u8"
}

def download_file(url, filename):
    """Download file with full debug + hardcore error handling"""
    try:
        log.info(f"[DEBUG] Starting download: {url}")
        with requests.get(url, stream=True, timeout=None) as r:
            try:
                r.raise_for_status()
            except HTTPError as he:
                msg = f"HTTP error: {he} | Status: {r.status_code} | Headers: {r.headers}"
                log.error(msg)
                return msg

            total = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = downloaded / total * 100
                            log.info(f"Downloaded: {percent:.2f}%")
        msg = f"Download finished: {filename}"
        log.info(msg)
        return msg

    except ConnectionError as ce:
        msg = f"Connection failed: {ce}"
        log.error(msg)
        return msg
    except Timeout as te:
        msg = f"Request timed out: {te}"
        log.error(msg)
        return msg
    except RequestException as e:
        msg = f"Download failed: {e}"
        log.error(msg)
        return msg

@Bot.on_message(filters.command("testdl") & filters.me)
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
    await message.reply_text(f"Starting download for {choice}...")

    # Download file
    result = download_file(url, filename)

    # Send result to Telegram PM
    await message.reply_text(f"Result: {result}")

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)