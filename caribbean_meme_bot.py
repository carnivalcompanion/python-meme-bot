# ------------------------------------------------------------------------------
# Caribbean Meme Bot (Render-ready)
# ------------------------------------------------------------------------------
import os
import random
import time
import logging
import schedule
import textwrap
from datetime import datetime, timedelta
from threading import Thread

from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from dotenv import load_dotenv
from flask import Flask

# ------------------------------------------------------------------------------
# Flask keep-alive
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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("caribbean_meme_bot")

load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

TRIVIA_FILE = "trivia.txt"
SLANG_FILE = "slang.txt"
PROFILE_IMG = "placeholder.jpg"

# ------------------------------------------------------------------------------
# Fonts (FreeSans)
# ------------------------------------------------------------------------------
def load_fonts():
    try:
        name_font = ImageFont.truetype("FreeSansBold.ttf", 52)
        handle_font = ImageFont.truetype("FreeSans.ttf", 40)
        text_font = ImageFont.truetype("FreeSans.ttf", 64)
        return name_font, handle_font, text_font
    except Exception as e:
        logger.warning(f"⚠️ FreeSans not found, fallback to default: {e}")
        f = ImageFont.load_default()
        return f, f, f

NAME_FONT, HANDLE_FONT, TEXT_FONT = load_fonts()

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def ensure_image_size(image_path, expected_size=(1080, 1350)):
    try:
        img = Image.open(image_path)
        if img.size != expected_size:
            logger.warning(f"🔄 Resizing {img.size} -> {expected_size}")
            img = img.resize(expected_size, Image.Resampling.LANCZOS)
            img.save(image_path, "JPEG", quality=95)
    except Exception as e:
        logger.error(f"Image resize failed: {e}")

def login_user(client: Client) -> bool:
    try:
        if os.path.exists("session.json"):
            client.load_settings("session.json")
            client.login(USERNAME, PASSWORD)
            logger.info("Logged in using session.json ✅")
        else:
            logger.info("No session.json, logging in fresh...")
            client.login(USERNAME, PASSWORD)
            client.dump_settings("session.json")
            logger.info("New session.json saved ✅")

        return bool(client.user_id)
    except Exception as e:
        logger.error(f"Login failed ❌: {e}")
        return False

def read_content(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

# ------------------------------------------------------------------------------
# Image Generator (Twitter-style dark post)
# ------------------------------------------------------------------------------
def create_dark_text_post(text: str, output_path="post.jpg") -> str:
    width, height = 1080, 1350
    bg_color = (21, 32, 43)  # Twitter dark background
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    display_name = "Carnival Companion"
    handle = "@carnivalcompanion · now"

    x_margin = 80
    y = 250
    pfp_size = 100

    # Profile picture (circle left)
    try:
        if os.path.exists(PROFILE_IMG):
            pfp = Image.open(PROFILE_IMG).convert("RGB").resize((pfp_size, pfp_size))
            mask = Image.new("L", (pfp_size, pfp_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, pfp_size, pfp_size), fill=255)
            image.paste(pfp, (x_margin, y), mask)
        else:
            draw.ellipse((x_margin, y, x_margin+pfp_size, y+pfp_size),
                         fill=(29, 155, 240))
    except Exception as e:
        logger.warning(f"Profile image error: {e}")
        draw.ellipse((x_margin, y, x_margin+pfp_size, y+pfp_size),
                     fill=(29, 155, 240))

    # Display name + handle
    draw.text((x_margin+120, y), display_name, font=NAME_FONT, fill=(255, 255, 255))
    draw.text((x_margin+120, y+60), handle, font=HANDLE_FONT, fill=(136, 153, 166))

    # Main wrapped text
    wrapped = textwrap.wrap(text, width=30)
    y_text = y + 160
    for line in wrapped:
        draw.text((x_margin, y_text), line, font=TEXT_FONT, fill=(255, 255, 255))
        y_text += 74  # tighter spacing than before

    image.save(output_path, "JPEG", quality=95)
    ensure_image_size(output_path, (width, height))
    return output_path

# ------------------------------------------------------------------------------
# Posting logic
# ------------------------------------------------------------------------------
def create_and_post(cl: Client):
    try:
        trivia = read_content(TRIVIA_FILE)
        slang = read_content(SLANG_FILE)
        if not trivia and not slang:
            logger.error("❌ No content in trivia.txt or slang.txt")
            return

        content = random.choice(trivia or slang)
        logger.info(f"📄 Selected: {content}")

        filename = f"post_{int(time.time())}.jpg"
        path = create_dark_text_post(content, filename)
        caption = f"{content}\n\n#CarnivalCompanion #Caribbean #IslandLife #Trivia"

        try:
            cl.photo_upload(path, caption)
            logger.info("✅ Post successful")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            if login_user(cl):
                cl.photo_upload(path, caption)
                logger.info("✅ Retry post successful")

        if os.path.exists(path):
            os.remove(path)
            logger.info("🗑️ Temp file removed")

        schedule_next_post(cl)

    except LoginRequired:
        logger.info("🔐 Session expired, re-login...")
        if login_user(cl):
            schedule_next_post(cl)
    except Exception as e:
        logger.error(f"Error in posting: {e}")
        time.sleep(300)
        schedule_next_post(cl)

def get_random_peak_time():
    now = datetime.now()
    peaks = [(9, 11), (17, 19), (20, 22)]
    start, end = random.choice(peaks)
    t = now.replace(hour=random.randint(start, end-1),
                    minute=random.randint(0, 59),
                    second=0, microsecond=0)
    if t <= now:
        t += timedelta(days=1)
    return t

def schedule_next_post(cl: Client):
    next_time = get_random_peak_time()
    delay = (next_time - datetime.now()).total_seconds()
    logger.info(f"📅 Next post at {next_time} (~{delay/3600:.1f}h)")
    schedule.clear()
    schedule.every(delay).seconds.do(lambda: create_and_post(cl))

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main():
    logger.info("🚀 Starting Caribbean Meme Bot...")
    keep_alive()

    if not USERNAME or not PASSWORD:
        logger.error("❌ Missing IG credentials in environment")
        return

    cl = Client()
    cl.delay_range = [1, 3]

    if not login_user(cl):
        logger.error("❌ Login failed")
        return

    logger.info("✅ Bot ready, posting first meme...")
    create_and_post(cl)

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("⏹️ Stopped by user")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()
