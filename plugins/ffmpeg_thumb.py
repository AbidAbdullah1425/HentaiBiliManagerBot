import os 
import subprocess
import logging
from typing import Optional
from config import LOGGER

logger = LOGGER("ffmpeg_py")


async def generate_video_thumbnail(video_path: str) -> Optional[str]:
    try:
        # Create output filename
        thumbnail_path = os.path.join(os.getcwd(), "thumb.jpg")
        
        # Get video duration using ffprobe
        duration_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Video Duration Exporter Failed! (ffprobe)\n\n {result.stderr}")
            await message.reply_text(f"Video Duration Exporter Failed! (ffprobe)\n\n {result.stderr}")
            
        try:
            duration = float(result.stdout.strip())
            # Take thumbnail at 75% of video duration
            timestamp = duration * 0.75 # Max 2.5 minutes in
        except ValueError:
            timestamp = 5  # Default to 5 seconds if duration parsing fails
            
        # Generate thumbnail using ffmpeg
        thumbnail_cmd = [
          "ffmpeg",
          "-ss", str(timestamp),  # Seek to timestamp
          "-i", video_path,       # Input file
          "-vf", "scale=480:-1:flags=lanczos",  # Better quality scaling, 480p width
          "-vframes", "1",        # Extract 1 frame
          "-q:v", "1",           # Highest quality (1-31, lower is better)
          "-pix_fmt", "yuv420p", # Widely compatible pixel format
          "-compression_level", "6", # Good compression (0-9)
          "-preset", "medium",    # Balance between speed and quality
          "-y",                   # Overwrite output file
          thumbnail_path
        ]
        
        process = subprocess.run(thumbnail_cmd, capture_output=True)
        if process.returncode != 0:
            logger.error(f"Thumbnail generation failed!\n\n {process.stderr}")
            await message.reply_text(f"Thumbnail generation failed!\n\n {process.stderr}")
            
        if os.path.exists(thumbnail_path):
            logger.info(f"Thumbnail generated: {thumbnail_path}")
            return thumbnail_path
            
        await message.reply_text(f"Thumbnail generated: {thumbnail_path}")
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        await message.reply_text(f"Error generating thumbnail: {str(e)}")