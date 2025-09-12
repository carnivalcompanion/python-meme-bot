# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import os
import random
import time
import logging
import schedule
import textwrap
from datetime import datetime, timedelta
from threading import Thread

# Pillow
from PIL import Image, ImageDraw, ImageFont

# Instagram client
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

# Env
from dotenv import load_dotenv

# Flask
from flask import Flask

# ------------------------------------------------------------------------------
# Flask keep-alive server
# ------------------------------------------------------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Python Meme Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("caribbean_meme_bot")

load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

TRIVIA_FILE = "trivia.txt"
SLANG_FILE = "slang.txt"
PROFILE_IMG = "placeholder.jpg"

# Font paths - OpenSans Condensed Medium
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "OpenSans_Condensed-Medium.ttf")

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def login_user(client: Client) -> bool:
    """Try session.json first, fallback to fresh login."""
    try:
        if os.path.exists("session.json"):
            client.load_settings("session.json")
            client.login(USERNAME, PASSWORD)
            logger.info("Logged in using saved session.json ✅")
        else:
            logger.info("No saved session.json, logging in fresh...")
            client.login(USERNAME, PASSWORD)
            client.dump_settings("session.json")
            logger.info("New session.json saved ✅")

        if client.user_id:
            logger.info("Instagram login success 🎉")
            return True
        return False
    except Exception as e:
        logger.error(f"Login failed ❌: {e}")
        return False

def read_content(file_path: str) -> list[str]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

# ------------------------------------------------------------------------------
# Image Generator (clean + bold)
# ------------------------------------------------------------------------------
def create_dark_text_post(text: str, output_path="post.jpg") -> str:
    width, height = 1080, 1350
    image = Image.new("RGB", (width, height), (21, 32, 43))  # Dark background
    draw = ImageDraw.Draw(image)

    # Improved font handling with multiple fallbacks - OpenSans focused
    font_size = 72
    try:
        # First try: Our preferred OpenSans font
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
            logger.info("Using OpenSans_Condensed-Medium.ttf from project fonts")
        except IOError:
            # Second try: System might have OpenSans installed
            try:
                font = ImageFont.truetype("OpenSans-CondensedMedium.ttf", font_size)
                logger.info("Using system OpenSans-CondensedMedium.ttf")
            except IOError:
                # Third try: Alternative naming
                try:
                    font = ImageFont.truetype("OpenSansCondensed-Medium.ttf", font_size)
                    logger.info("Using OpenSansCondensed-Medium.ttf")
                except IOError:
                    # Fourth try: Common Linux fonts as fallback
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                        logger.info("Using DejaVuSans-Bold as fallback")
                    except IOError:
                        # Final fallback to default font
                        logger.warning("Using default font - may affect image quality")
                        font = ImageFont.load_default()
                        # Try to set size for default font
                        try:
                            font.size = font_size
                        except:
                            pass
    except Exception as e:
        logger.warning(f"Font loading issues: {e}")
        font = ImageFont.load_default()

    logger.info(f"Font properties: size={getattr(font, 'size', 'unknown')}")

    # Wrap text with appropriate width
    wrapped = textwrap.wrap(text, width=18)
    logger.info(f"Text wrapped into {len(wrapped)} lines")

    # Calculate text position to center vertically
    line_height = 80  # Fixed line height for consistency
    total_text_height = len(wrapped) * line_height
    y = (height - total_text_height) // 2
    
    logger.info(f"Text positioning: y={y}, total_height={total_text_height}")
    
    for line in wrapped:
        # Calculate text width to center horizontally
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_height

    # Profile image handling
    try:
        pfp = Image.open(PROFILE_IMG).convert("RGB")
        # Resize with proper aspect ratio
        pfp_size = (120, 120)
        pfp = pfp.resize(pfp_size, Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new("L", pfp_size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, pfp_size[0], pfp_size[1]), fill=255)
        
        # Position profile image
        image.paste(pfp, (80, 100), mask)
        logger.info("Profile image added successfully")
    except Exception as e:
        logger.warning(f"Profile image not loaded: {e}")

    image.save(output_path, "JPEG", quality=95)
    
    # Debug: Check image dimensions
    img = Image.open(output_path)
    logger.info(f"Final image size: {img.size}")  # Should be (1080, 1350)
    
    return output_path

# ------------------------------------------------------------------------------
# Posting Logic
# ------------------------------------------------------------------------------
def create_and_post(cl: Client):
    try:
        trivia = read_content(TRIVIA_FILE)
        slang = read_content(SLANG_FILE)
        if not trivia and not slang:
            logger.error("No content in trivia.txt or slang.txt")
            return

        content = random.choice(trivia or slang)
        logger.info(f"Selected content: {content[:50]}...")
        raw_path = create_dark_text_post(content, f"post_{int(time.time())}.jpg")
        caption = f"{content}\n\n#CarnivalCompanion #Caribbean"

        try:
            cl.photo_upload(raw_path, caption)
            logger.info(f"✅ Posted: {content[:50]}...")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            if login_user(cl):
                cl.photo_upload(raw_path, caption)

        os.remove(raw_path)
        logger.info(f"🗑️ Removed temp: {raw_path}")

        schedule_next_post(cl)
    except LoginRequired:
        logger.info("Session expired — re-logging...")
        if login_user(cl):
            schedule_next_post(cl)
    except Exception as e:
        logger.error(f"Error in posting loop: {e}")
        time.sleep(300)
        schedule_next_post(cl)

def get_random_peak_time() -> datetime:
    now = datetime.now()
    peak_windows = [(9, 11), (17, 19), (20, 22)]
    start, end = random.choice(peak_windows)
    post_time = now.replace(hour=random.randint(start, end-1), minute=random.randint(0, 59), second=0)
    if post_time <= now:
        post_time += timedelta(days=1)
    return post_time

def schedule_next_post(cl: Client):
    next_time = get_random_peak_time()
    delay = (next_time - datetime.now()).total_seconds()
    logger.info(f"📅 Next post scheduled: {next_time} (~{delay/3600:.1f}h)")
    schedule.clear()
    schedule.every(delay).seconds.do(lambda: create_and_post(cl))

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main():
    keep_alive()
    cl = Client()
    cl.delay_range = [1, 3]

    if not login_user(cl):
        return

    logger.info("Bot started ✅ First post now...")
    create_and_post(cl)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()