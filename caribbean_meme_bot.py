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

# Colors (Twitter dark mode)
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


def create_twitter_style_image(text: str, content_type: str, output_path="post.jpg") -> str:
    """Generate a clean Twitter-style post image (720x720 square with Twitter blue theme)."""
    width, height = 720, 720  # Square format
    image = Image.new("RGB", (width, height), TWITTER_BG)
    draw = ImageDraw.Draw(image)

    # Fonts - scaled for 720x720
    try:
        name_font = ImageFont.truetype("arialbd.ttf", 40)
        handle_font = ImageFont.truetype("arial.ttf", 32)
        text_font = ImageFont.truetype("arial.ttf", 44)
        small_font = ImageFont.truetype("arial.ttf", 32)
    except:
        # Fallback to default fonts if custom ones aren't available
        name_font = ImageFont.load_default()
        handle_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Profile section at top
    profile_size = 80
    profile_x = 50
    profile_y = 50

    # Draw profile picture (circle)
    try:
        pfp_path = os.path.join(os.path.dirname(__file__), PROFILE_IMG)
        pfp = Image.open(pfp_path).convert("RGB").resize((profile_size, profile_size))
        mask = Image.new("L", (profile_size, profile_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, profile_size, profile_size), fill=255)
        image.paste(pfp, (profile_x, profile_y), mask)
    except Exception as e:
        logger.error(f"⚠️ Could not load profile image: {e}")
        draw.ellipse([profile_x, profile_y, profile_x + profile_size, profile_y + profile_size], fill=TWITTER_BLUE)

    # Account name and handle
    draw.text((profile_x + profile_size + 15, profile_y + 8), "Carnival Companion", fill=TWITTER_TEXT, font=name_font)
    draw.text((profile_x + profile_size + 15, profile_y + 52), "@CarnivalCompanion · 2h", fill=TWITTER_MUTED, font=handle_font)

    # Post content - centered with proper spacing
    content_x = profile_x
    content_y = profile_y + profile_size + 40
    
    # Wrap text to fit within image width
    wrapped_lines = textwrap.wrap(text, width=28)
    
    # Draw each line of text
    for line in wrapped_lines:
        # Center each line of text
        line_width = text_font.getlength(line)
        line_x = (width - line_width) // 2
        draw.text((line_x, content_y), line, font=text_font, fill=TWITTER_TEXT)
        content_y += text_font.size + 15

    # Engagement section (likes, retweets) - SIMPLIFIED VERSION
    engagement_y = content_y + 40
    
    # Simple text-based engagement (no icons that could cause red dots)
    likes = random.randint(500, 5000)
    retweets = random.randint(500, 5000)
    
    engagement_text = f"{likes:,} likes    {retweets:,} retweets"
    engagement_width = small_font.getlength(engagement_text)
    engagement_x = (width - engagement_width) // 2
    
    draw.text((engagement_x, engagement_y), engagement_text, fill=TWITTER_MUTED, font=small_font)

    # Hashtags at the bottom
    hashtag_y = engagement_y + 50
    hashtags = get_peak_hashtags()
    hashtag_width = small_font.getlength(hashtags)
    hashtag_x = (width - hashtag_width) // 2
    draw.text((hashtag_x, hashtag_y), hashtags, fill=TWITTER_BLUE, font=small_font)

    image.save(output_path)
    logger.info(f"Created clean Twitter-style image: {output_path}")
    return output_path

def prepare_image(path: str, out_path: str) -> str:
    """Crop + resize image to 720x720 for Instagram feed posts."""
    img = Image.open(path).convert("RGB")

    target_w, target_h = 720, 720  # Square format

    # Current aspect ratio
    w, h = img.size
    current_ratio = w / h

    if current_ratio > 1:
        # Image too wide → crop width
        new_w = h
        left = (w - new_w) // 2
        right = left + new_w
        img = img.crop((left, 0, right, h))
    else:
        # Image too tall → crop height
        new_h = w
        top = (h - new_h) // 2
        bottom = top + new_h
        img = img.crop((0, top, w, bottom))

    # Final resize to 720x720
    img = img.resize((target_w, target_h), Image.LANCZOS)
    img.save(out_path, "JPEG", quality=95)
    return out_path


# ------------------------------------------------------------------------------
# Posting Logic
# ------------------------------------------------------------------------------

def get_random_peak_time() -> datetime:
    """Return a random peak posting time for the next day if needed."""
    now = datetime.now()
    peak_windows = [(9, 11), (17, 19), (20, 22)]  # morning, evening, late
    start, end = random.choice(peak_windows)
    hour = random.randint(start, end - 1)
    minute = random.randint(0, 59)
    post_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if post_time <= now:
        post_time += timedelta(days=1)
    return post_time


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

            # Create the Twitter-style image
            image_path = create_twitter_style_image(content, ctype, f"post_{int(time.time())}.jpg")
            
            # For Instagram, we'll use just hashtags in the caption
            caption = get_peak_hashtags()

            try:
                cl.photo_upload(image_path, caption)
                logger.info(f"Posted: {content[:50]}...")
            except Exception as e:
                logger.error(f"Failed to upload: {e}")
                if login_user(cl):
                    try:
                        cl.photo_upload(image_path, caption)
                        logger.info(f"Posted after relogin: {content[:50]}...")
                    except Exception as e2:
                        logger.error(f"Failed again after relogin: {e2}")
                continue

            try:
                os.remove(image_path)
                logger.info(f"Removed temporary image: {image_path}")
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