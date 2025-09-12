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
# Setup Logger FIRST
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("caribbean_meme_bot")

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
# Load environment variables
# ------------------------------------------------------------------------------
load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

TRIVIA_FILE = "trivia.txt"
SLANG_FILE = "slang.txt"
PROFILE_IMG = "placeholder.jpg"

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def ensure_image_size(image_path, expected_size=(1080, 1350)):
    """Ensure image is exactly the expected size"""
    try:
        img = Image.open(image_path)
        if img.size != expected_size:
            logger.warning(f"🔄 Resizing image from {img.size} to {expected_size}")
            img_resized = img.resize(expected_size, Image.Resampling.LANCZOS)
            img_resized.save(image_path, "JPEG", quality=95)
            return True
        return False
    except Exception as e:
        logger.error(f"Error in ensure_image_size: {e}")
        return False

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
# Image Generator - EXACT Preview Style
# ------------------------------------------------------------------------------
def create_dark_text_post(text: str, output_path="post.jpg") -> str:
    # Canvas size (Instagram 4:5 ratio)
    width, height = 1080, 1350
    image = Image.new("RGB", (width, height), (21, 32, 43))  # dark background
    draw = ImageDraw.Draw(image)

    # Fonts - EXACT sizes from preview
    try:
        # Try Arial fonts first
        name_font = ImageFont.truetype("Arial Bold.ttf", 52)
        handle_font = ImageFont.truetype("Arial.ttf", 40)
        text_font = ImageFont.truetype("Arial.ttf", 64)
        header_font = ImageFont.truetype("Arial Bold.ttf", 80)
    except:
        try:
            # Try alternative font names
            name_font = ImageFont.truetype("arialbd.ttf", 52)
            handle_font = ImageFont.truetype("arial.ttf", 40)
            text_font = ImageFont.truetype("arial.ttf", 64)
            header_font = ImageFont.truetype("arialbd.ttf", 80)
        except:
            # Final fallback to default font
            name_font = handle_font = text_font = header_font = ImageFont.load_default()

    # EXACT text from preview
    display_name = "Carnival Companion"
    handle = "@carnivalcompanion · now"

    # EXACT positions from preview
    y = 250
    x_margin = 80
    pfp_size = 100

    # 1. "CARNIVAL" HEADER - EXACT from preview (top center)
    header_text = "CARNIVAL"
    try:
        bbox = draw.textbbox((0, 0), header_text, font=header_font)
        header_width = bbox[2] - bbox[0]
        header_x = (width - header_width) // 2
        draw.text((header_x, 100), header_text, font=header_font, fill=(255, 255, 255))
    except:
        # Manual fallback positioning
        draw.text((width//2 - 180, 100), header_text, fill=(255, 255, 255))

    # 2. PROFILE PICTURE - EXACT position from preview (left side)
    try:
        if os.path.exists(PROFILE_IMG):
            pfp = Image.open(PROFILE_IMG).convert("RGB").resize((pfp_size, pfp_size))
            # Create circular mask
            mask = Image.new("L", (pfp_size, pfp_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, pfp_size, pfp_size), fill=255)
            image.paste(pfp, (x_margin, y), mask)
        else:
            # Draw blue placeholder circle (EXACT from preview)
            draw.ellipse((x_margin, y, x_margin+pfp_size, y+pfp_size), fill=(29, 155, 240))
    except Exception as e:
        logger.warning(f"Profile image error: {e}")
        draw.ellipse((x_margin, y, x_margin+pfp_size, y+pfp_size), fill=(29, 155, 240))

    # 3. DISPLAY NAME - EXACT from preview (right of profile)
    draw.text((x_margin+120, y), display_name, font=name_font, fill=(255, 255, 255))

    # 4. HANDLE - EXACT from preview (below name, gray color)
    draw.text((x_margin+120, y+60), handle, font=handle_font, fill=(136, 153, 166))

    # 5. MAIN TEXT - EXACT wrapping and positioning from preview
    # Wrap text EXACTLY like preview (width=30 characters)
    wrapped_lines = textwrap.wrap(text, width=30)
    y_text = y + 160  # EXACT spacing from preview
    
    for line in wrapped_lines:
        # LEFT-ALIGNED text at exact position from preview
        draw.text((x_margin, y_text), line, font=text_font, fill=(255, 255, 255))
        # EXACT line spacing from preview
        y_text += 84  # 64px font + 20px spacing = 84px

    # Save image
    image.save(output_path, "JPEG", quality=95)
    logger.info(f"💾 Image saved to: {output_path}")
    
    # Force correct dimensions
    ensure_image_size(output_path, (width, height))
    
    return output_path

# ------------------------------------------------------------------------------
# Posting Logic
# ------------------------------------------------------------------------------
def create_and_post(cl: Client):
    try:
        trivia = read_content(TRIVIA_FILE)
        slang = read_content(SLANG_FILE)
        if not trivia and not slang:
            logger.error("❌ No content in trivia.txt or slang.txt")
            return

        content = random.choice(trivia or slang)
        logger.info(f"📄 Selected content: {content}")
        
        timestamp = int(time.time())
        raw_path = f"post_{timestamp}.jpg"
        
        raw_path = create_dark_text_post(content, raw_path)
        caption = f"{content}\n\n#CarnivalCompanion #Caribbean #IslandLife #Trivia"

        try:
            cl.photo_upload(raw_path, caption)
            logger.info(f"✅ Posted successfully!")
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            if login_user(cl):
                try:
                    cl.photo_upload(raw_path, caption)
                    logger.info(f"✅ Re-upload successful after re-login")
                except Exception as retry_error:
                    logger.error(f"❌ Re-upload also failed: {retry_error}")

        # Clean up temp file
        if os.path.exists(raw_path):
            os.remove(raw_path)
            logger.info(f"🗑️ Removed temp file")

        schedule_next_post(cl)
        
    except LoginRequired:
        logger.info("🔐 Session expired — re-logging...")
        if login_user(cl):
            schedule_next_post(cl)
    except Exception as e:
        logger.error(f"❌ Error in posting loop: {e}")
        time.sleep(300)
        schedule_next_post(cl)

def get_random_peak_time() -> datetime:
    now = datetime.now()
    peak_windows = [(9, 11), (17, 19), (20, 22)]
    start, end = random.choice(peak_windows)
    post_time = now.replace(
        hour=random.randint(start, end-1), 
        minute=random.randint(0, 59), 
        second=0, 
        microsecond=0
    )
    if post_time <= now:
        post_time += timedelta(days=1)
    return post_time

def schedule_next_post(cl: Client):
    next_time = get_random_peak_time()
    delay = (next_time - datetime.now()).total_seconds()
    logger.info(f"📅 Next post scheduled: {next_time} (~{delay/3600:.1f} hours)")
    schedule.clear()
    schedule.every(delay).seconds.do(lambda: create_and_post(cl))

# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------
def main():
    logger.info("🚀 Starting Caribbean Meme Bot...")
    keep_alive()
    
    # Verify environment
    if not USERNAME or not PASSWORD:
        logger.error("❌ Missing Instagram credentials in environment variables")
        return
    
    cl = Client()
    cl.delay_range = [1, 3]

    if not login_user(cl):
        logger.error("❌ Failed to login to Instagram")
        return

    logger.info("✅ Bot started successfully! First post now...")
    create_and_post(cl)

    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("⏹️ Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()