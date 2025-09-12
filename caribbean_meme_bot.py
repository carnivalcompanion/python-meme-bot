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

# Colors for Instagram-style images
INSTAGRAM_BG = (255, 255, 255)  # White background
INSTAGRAM_TEXT = (0, 0, 0)      # Black text
INSTAGRAM_MUTED = (142, 142, 142)  # Gray text
INSTAGRAM_BLUE = (56, 151, 240)    # Instagram blue

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


def create_instagram_style_image(text: str, content_type: str, output_path="post.jpg") -> str:
    """Generate an Instagram-style post image (1080x1080 square)."""
    width, height = 1080, 1080  # Square format for Instagram
    image = Image.new("RGB", (width, height), INSTAGRAM_BG)
    draw = ImageDraw.Draw(image)

    # Fonts - using larger sizes for better readability
    try:
        # Try to load fonts - adjust these based on what's available on your system
        name_font = ImageFont.truetype("arialbd.ttf", 42)
        handle_font = ImageFont.truetype("arial.ttf", 34)
        text_font = ImageFont.truetype("arial.ttf", 46)  # Larger text size
        small_font = ImageFont.truetype("arial.ttf", 32)
        engagement_font = ImageFont.truetype("arial.ttf", 28)
    except:
        # Fallback to default fonts if custom ones aren't available
        name_font = ImageFont.load_default()
        handle_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        engagement_font = ImageFont.load_default()

    # Profile section at top
    profile_size = 80
    profile_x = 40
    profile_y = 40

    # Draw profile picture (circle)
    try:
        pfp_path = os.path.join(os.path.dirname(__file__), PROFILE_IMG)
        pfp = Image.open(pfp_path).convert("RGB").resize((profile_size, profile_size))
        mask = Image.new("L", (profile_size, profile_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, profile_size, profile_size), fill=255)
        image.paste(pfp, (profile_x, profile_y), mask)
    except Exception as e:
        logger.error(f"⚠️ Could not load profile image: {e}")
        draw.ellipse([profile_x, profile_y, profile_x + profile_size, profile_y + profile_size], fill=INSTAGRAM_BLUE)

    # Account name and handle
    draw.text((profile_x + profile_size + 15, profile_y + 5), "carnivalcompanion", fill=INSTAGRAM_TEXT, font=name_font)
    draw.text((profile_x + profile_size + 15, profile_y + 45), "@carnivalcompanion", fill=INSTAGRAM_MUTED, font=handle_font)

    # More options icon (three dots)
    options_x = width - 50
    draw.ellipse([options_x, profile_y + 15, options_x + 4, profile_y + 19], fill=INSTAGRAM_TEXT)
    draw.ellipse([options_x, profile_y + 25, options_x + 4, profile_y + 29], fill=INSTAGRAM_TEXT)
    draw.ellipse([options_x, profile_y + 35, options_x + 4, options_x + 39], fill=INSTAGRAM_TEXT)

    # Post content - centered with proper spacing
    content_x = 40
    content_y = profile_y + profile_size + 50
    
    # Wrap text to fit within image width
    wrapped_lines = textwrap.wrap(text, width=35)  # Adjust character count for line breaks
    
    # Draw each line of text
    for line in wrapped_lines:
        draw.text((content_x, content_y), line, font=text_font, fill=INSTAGRAM_TEXT)
        content_y += text_font.size + 15  # Increase line spacing

    # Engagement section (likes, comments, etc.)
    engagement_y = content_y + 40
    
    # Likes count
    likes = random.randint(500, 5000)
    draw.text((content_x, engagement_y), f"{likes:,}", fill=INSTAGRAM_TEXT, font=engagement_font)
    
    # Comments icon and count
    comments = random.randint(10, 500)
    draw.text((content_x + 100, engagement_y), f"{comments}", fill=INSTAGRAM_TEXT, font=engagement_font)
    
    # Share icon (paper airplane)
    draw.text((content_x + 200, engagement_y), "314", fill=INSTAGRAM_TEXT, font=engagement_font)  # Static share count
    
    # Bookmark icon
    bookmark_x = width - 50
    draw.rectangle([bookmark_x, engagement_y, bookmark_x + 20, engagement_y + 25], outline=INSTAGRAM_TEXT, width=2)

    # Timestamp and location
    timestamp_y = engagement_y + 40
    draw.text((content_x, timestamp_y), "2 hours ago", fill=INSTAGRAM_MUTED, font=small_font)
    
    # Add some hashtags at the bottom
    hashtag_y = timestamp_y + 40
    draw.text((content_x, hashtag_y), get_peak_hashtags(), fill=INSTAGRAM_BLUE, font=small_font)

    image.save(output_path)
    logger.info(f"Created Instagram-style image: {output_path}")
    return output_path


def prepare_image(path: str, out_path: str) -> str:
    """Crop + resize image to 1080x1080 for Instagram feed posts."""
    img = Image.open(path).convert("RGB")

    target_w, target_h = 1080, 1080  # Square format

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

    # Final resize to 1080x1080
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

            # Create the Instagram-style image
            image_path = create_instagram_style_image(content, ctype, f"post_{int(time.time())}.jpg")
            
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