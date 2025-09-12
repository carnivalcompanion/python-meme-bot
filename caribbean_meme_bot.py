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

# Pillow (image generation)
from PIL import Image, ImageDraw, ImageFont

# Instagram client
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

# Environment variables
from dotenv import load_dotenv

# Flask for keep-alive server
from flask import Flask

# ------------------------------------------------------------------------------
# Flask keep-alive server
# ------------------------------------------------------------------------------

app = Flask(__name__)

@app.route('/')
def home():
    return "Python Bot is alive!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("caribbean_meme_bot")

# Load environment variables
load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

# File paths
TRIVIA_FILE = "trivia.txt"
SLANG_FILE = "slang.txt"
PROFILE_IMG = "placeholder.jpg"

# Colors (Twitter/X style dark mode)
TWITTER_BG = (21, 32, 43)
TWITTER_TEXT = (255, 255, 255)
TWITTER_MUTED = (136, 153, 166)
TWITTER_BLUE = (29, 161, 242)

# Hashtags
CARIBBEAN_HASHTAGS = [
    "#Caribbean", "#WestIndian", "#IslandLife", "#TropicalVibes",
    "#CaribbeanCulture", "#Soca", "#Reggae", "#Dancehall",
    "#CaribbeanFood", "#Carnival", "#Steelpan", "#CaribbeanMusic",
    "#TrinidadCarnival", "#Jamaica", "#Barbados", "#Tobago",
    "#CaribbeanTravel", "#CaribbeanStyle", "#CaribbeanLife",
    "#CaribbeanVibes", "#WestIndies", "#IslandTime", "#CaribbeanDream"
]

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def login_user(client: Client) -> bool:
    """Log into Instagram."""
    try:
        try:
            client.load_settings("session.json")
            client.login(USERNAME, PASSWORD)
            logger.info("Logged in using saved session")
        except FileNotFoundError:
            logger.info("No saved session found, logging in fresh")
            client.login(USERNAME, PASSWORD)
            client.dump_settings("session.json")

        if client.user_id:
            logger.info("Logged in successfully")
            return True
        return False
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False


def read_content(file_path: str) -> list[str]:
    """Read lines from a file, stripping blanks."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
        return []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []


def get_peak_hashtags() -> str:
    """Get 4 random hashtags plus #CarnivalCompanion."""
    return " ".join(random.sample(CARIBBEAN_HASHTAGS, 4)) + " #CarnivalCompanion"


def create_twitter_style_post(text: str, output_path="post.jpg") -> str:
    """Generate a clean X/Twitter-style post with profile image, left-aligned text."""
    width, height = 1080, 1350  # Instagram 4:5 portrait
    image = Image.new("RGB", (width, height), TWITTER_BG)
    draw = ImageDraw.Draw(image)

    # Fonts
    try:
        name_font = ImageFont.truetype("arialbd.ttf", 48)
        handle_font = ImageFont.truetype("arial.ttf", 36)
        text_font = ImageFont.truetype("arial.ttf", 64)  # large readable text
    except:
        name_font = handle_font = text_font = ImageFont.load_default()

    # Profile circle
    profile_size = 110
    try:
        pfp = Image.open(PROFILE_IMG).convert("RGB").resize((profile_size, profile_size))
        mask = Image.new("L", (profile_size, profile_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, profile_size, profile_size), fill=255)
        image.paste(pfp, (70, 70), mask)
    except:
        draw.ellipse([70, 70, 70+profile_size, 70+profile_size], fill=TWITTER_BLUE)

    # Name + handle
    draw.text((200, 80), "Carnival Companion", fill=TWITTER_TEXT, font=name_font)
    draw.text((200, 140), "@CarnivalCompanion", fill=TWITTER_MUTED, font=handle_font)

    # Post text (left aligned, slightly lower in the frame)
    wrapped_lines = textwrap.wrap(text, width=28)
    y_text = 300
    for line in wrapped_lines:
        draw.text((70, y_text), line, font=text_font, fill=TWITTER_TEXT)
        y_text += text_font.size + 25

    # Save
    image.save(output_path, "JPEG", quality=95)
    logger.info(f"✅ Created post: {output_path}")
    return output_path


def get_random_peak_time() -> datetime:
    now = datetime.now()
    peak_windows = [(9, 11), (17, 19), (20, 22)]
    start, end = random.choice(peak_windows)
    hour = random.randint(start, end - 1)
    minute = random.randint(0, 59)
    post_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if post_time <= now:
        post_time += timedelta(days=1)
    return post_time


def prepare_image(path: str, out_path: str) -> str:
    """Resize image to 1080x1350 for Instagram feed posts."""
    img = Image.open(path)
    img = img.convert("RGB")
    target_size = (1080, 1350)  # Instagram 4:5 ratio
    img = img.resize(target_size, Image.LANCZOS)
    img.save(out_path, "JPEG", quality=95)
    return out_path

# ------------------------------------------------------------------------------
# Posting Logic
# ------------------------------------------------------------------------------

def create_and_post(cl: Client):
    try:
        trivia_list = read_content(TRIVIA_FILE)
        slang_list = read_content(SLANG_FILE)
        if not trivia_list and not slang_list:
            logger.error("No content found in trivia.txt or slang.txt")
            return

        post_count = random.randint(1, 2)
        logger.info(f"Making {post_count} post(s) this session")

        for i in range(post_count):
            if random.choice([True, False]) and trivia_list:
                content, ctype = random.choice(trivia_list), "trivia"
            elif slang_list:
                content, ctype = random.choice(slang_list), "slang"
            else:
                content, ctype = random.choice(trivia_list), "trivia"

            raw_image_path = create_twitter_style_post(content, f"post_{int(time.time())}.jpg")
            prepared_path = prepare_image(raw_image_path, f"prepared_{int(time.time())}.jpg")
            caption = f"{content}\n\n{get_peak_hashtags()}"

            try:
                cl.photo_upload(prepared_path, caption)
                logger.info(f"Posted: {content[:50]}...")
            except Exception as e:
                logger.error(f"Failed to upload: {e}")
                if login_user(cl):
                    try:
                        cl.photo_upload(prepared_path, caption)
                        logger.info(f"Posted after relogin: {content[:50]}...")
                    except Exception as e2:
                        logger.error(f"Failed again after relogin: {e2}")
                continue

            try:
                os.remove(raw_image_path)
                os.remove(prepared_path)
                logger.info(f"Removed temporary images: {raw_image_path}, {prepared_path}")
            except:
                pass

            if i < post_count - 1:
                delay = random.randint(1800, 3600)
                logger.info(f"Waiting {delay//60} minutes before next post...")
                time.sleep(delay)

        schedule_next_post(cl)

    except LoginRequired:
        logger.info("Session expired, re-logging...")
        if login_user(cl):
            schedule_next_post(cl)
    except Exception as e:
        logger.error(f"Error in create_and_post: {e}")
        time.sleep(300)
        schedule_next_post(cl)


def schedule_next_post(cl: Client):
    next_time = get_random_peak_time()
    delay = (next_time - datetime.now()).total_seconds()
    logger.info(f"Next post scheduled for: {next_time} (in {delay/3600:.1f} hours)")

    schedule.clear()
    schedule.every(delay).seconds.do(lambda: create_and_post(cl))

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def main():
    keep_alive()  # Start the keep-alive server

    cl = Client()
    cl.delay_range = [1, 3]

    try:
        cl.load_settings("session.json")
    except FileNotFoundError:
        logger.info("No existing session file found")

    if not login_user(cl):
        logger.error("Failed to login. Check your credentials in .env file")
        return

    logger.info("Bot started ✅")
    logger.info("Posting immediately to verify setup...")
    create_and_post(cl)

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()
