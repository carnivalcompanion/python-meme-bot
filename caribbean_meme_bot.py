# ------------------------------------------------------------------------------
# Caribbean Meme Bot (Toggle Edition) - Easily switch between content modes
# ------------------------------------------------------------------------------
import os
import random
import time
import logging
import schedule
import textwrap
from datetime import datetime, timedelta
from threading import Thread
import json
import hashlib

from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv
from flask import Flask

# ------------------------------------------------------------------------------
# Configuration - EASY TOGGLE HERE
# ------------------------------------------------------------------------------
CONTENT_MODE = "trivia_only"  # ← CHANGE THIS TO SWITCH MODES
# Options: "trivia_only", "slang_only", "both"

# ------------------------------------------------------------------------------
# Flask app (health endpoint only)
# ------------------------------------------------------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Python Meme Bot is alive!"

@app.route("/health")
def health():
    return "OK"

# ------------------------------------------------------------------------------
# Stealth Configuration
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("caribbean_meme_bot")
logging.getLogger("instagrapi").setLevel(logging.WARNING)

load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

TRIVIA_FILE = "trivia.txt"
SLANG_FILE = "slang.txt"
PROFILE_IMG = "placeholder.jpg"
SESSION_DIR = os.getenv("SESSION_DIR", ".")  # optional persistence dir

# ------------------------------------------------------------------------------
# Human-like Behavior Simulation
# ------------------------------------------------------------------------------
class HumanBehavior:
    def __init__(self):
        self.last_action_time = 0
        self.action_count = 0
        self.daily_limit = random.randint(2, 4)
        self.startup_quick = True  # first post is fast

    def random_delay(self, min_sec=30, max_sec=120):
        if self.startup_quick:
            delay = random.uniform(0.2, 1.2)
            self.startup_quick = False
        else:
            delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def typing_delay(self, text):
        delay = len(text) * 0.1 + random.uniform(0.5, 2.0)
        time.sleep(delay)

    def get_human_like_delay_range(self):
        base_min = random.uniform(1.5, 3.5)
        base_max = random.uniform(4.5, 8.5)
        return [base_min, base_max]

    def should_take_break(self):
        self.action_count += 1
        if self.action_count % random.randint(3, 6) == 0:
            break_time = random.uniform(1800, 7200)  # 30min to 2hr
            logger.info(f"🧘 Taking human-like break for {break_time/60:.1f} minutes")
            time.sleep(break_time)
            return True
        return False

# ------------------------------------------------------------------------------
# Advanced Session Management - FIXED VERSION
# ------------------------------------------------------------------------------
def compute_version_code(app_version: str) -> str:
    """Extract digits from app_version to build version_code like '2690001875'"""
    return ''.join([c for c in app_version if c.isdigit()])

def create_device_settings():
    """Return a device dict that includes a version_code suitable for instagrapi.set_device."""
    devices = [
        {
            "app_version": "269.0.0.18.75",
            "android_version": 29,
            "android_release": "10.0",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "Samsung",
            "device": "SM-G973F",
            "model": "Galaxy S10",
            "cpu": "exynos9820"
        },
        {
            "app_version": "269.0.0.18.75",
            "android_version": 30,
            "android_release": "11.0",
            "dpi": "440dpi",
            "resolution": "1080x2160",
            "manufacturer": "Google",
            "device": "Pixel 4",
            "model": "Pixel 4",
            "cpu": "qualcomm"
        }
    ]
    chosen = random.choice(devices)
    # FIX: Ensure version_code is present as string (not int)
    chosen["version_code"] = compute_version_code(chosen["app_version"])
    return chosen

def save_secure_session(client: Client, username: str):
    """Save client.get_settings() to a username.session file (obfuscated)"""
    try:
        session_data = client.get_settings()
        session_str = json.dumps(session_data)
        encoded = session_str.encode('utf-8')
        filename = os.path.join(SESSION_DIR, f"{username}.session")
        with open(filename, 'wb') as f:
            f.write(encoded[::-1])
        return filename
    except Exception as e:
        logger.warning(f"Failed to save session: {e}")
        return None

def load_secure_session(client: Client, username: str):
    """Load username.session if exists and set into client"""
    target_file = os.path.join(SESSION_DIR, f"{username}.session")
    if not os.path.exists(target_file):
        # fallback to any .session file in dir
        session_files = [os.path.join(SESSION_DIR, f) for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
        if not session_files:
            return None
        target_file = max(session_files, key=os.path.getctime)

    try:
        with open(target_file, 'rb') as f:
            encoded_data = f.read()
        session_str = encoded_data[::-1].decode('utf-8')
        session_data = json.loads(session_str)
        client.set_settings(session_data)
        return True
    except Exception as e:
        logger.warning(f"Session load failed ({target_file}): {e}")
        return False

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
            logger.info(f"🔄 Resizing {img.size} -> {expected_size}")
            img = img.resize(expected_size, Image.Resampling.LANCZOS)
            img.save(image_path, "JPEG", quality=95)
    except Exception as e:
        logger.error(f"Image resize failed: {e}")

def advanced_login(client: Client, human_behavior: HumanBehavior) -> bool:
    """Advanced login: try load session, verify, otherwise fresh login with set_device."""
    try:
        human_behavior.random_delay(2, 6)

        if USERNAME:
            loaded = load_secure_session(client, USERNAME)
            if loaded:
                logger.info("Loaded existing session (attempting verify)...")
                try:
                    client.get_timeline_feed()
                    logger.info("Session verified ✅")
                    return True
                except (LoginRequired, ChallengeRequired, Exception) as e:
                    logger.info(f"Session verify failed: {e}. Will attempt fresh login.")

        device = create_device_settings()
        # FIX: Proper device setting with version_code
        logger.info(f"Setting device with version_code: {device.get('version_code')}")
        try:
            # Try full device settings first
            client.set_device(device)
        except Exception as e:
            logger.warning(f"Full device settings failed, trying minimal: {e}")
            # Fallback to minimal device settings
            minimal_device = {
                "app_version": device["app_version"],
                "android_version": device["android_version"],
                "android_release": device["android_release"],
                "version_code": device["version_code"]  # Keep version_code
            }
            try:
                client.set_device(minimal_device)
            except Exception as e2:
                logger.warning(f"Minimal device settings also failed: {e2}")
                # Last resort - just set the critical fields directly
                client.setting = device

        logger.info("Performing fresh login...")
        human_behavior.typing_delay(USERNAME if USERNAME else "")
        client.login(USERNAME, PASSWORD)

        saved = save_secure_session(client, USERNAME) if USERNAME else None
        if saved:
            logger.info(f"New session created and saved -> {saved}")
        else:
            logger.info("New session created (but saving failed)")

        human_behavior.random_delay(6, 14)
        return True

    except ChallengeRequired as e:
        logger.error(f"Challenge required: {e}")
        return False
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False

def read_content(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

# ------------------------------------------------------------------------------
# Image generation
# ------------------------------------------------------------------------------
def create_dark_text_post(text: str, output_path="post.jpg") -> str:
    width, height = 1080, 1350
    bg_color = (21, 32, 43)
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    display_name = "Carnival Companion"
    handle = "@carnivalcompanion · now"

    x_margin = 80
    y = 250
    pfp_size = 100

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

    draw.text((x_margin+120, y), display_name, font=NAME_FONT, fill=(255, 255, 255))
    draw.text((x_margin+120, y+60), handle, font=HANDLE_FONT, fill=(136, 153, 166))

    wrapped = textwrap.wrap(text, width=30)
    y_text = y + 160
    for line in wrapped:
        draw.text((x_margin, y_text), line, font=TEXT_FONT, fill=(255, 255, 255))
        y_text += 74

    image.save(output_path, "JPEG", quality=95)
    ensure_image_size(output_path, (width, height))
    return output_path

# ------------------------------------------------------------------------------
# Posting logic - TOGGLE VERSION
# ------------------------------------------------------------------------------
def get_content_pool():
    """Returns content based on the current CONTENT_MODE"""
    trivia = read_content(TRIVIA_FILE)
    slang = read_content(SLANG_FILE)
    
    if CONTENT_MODE == "trivia_only":
        logger.info("📚 Mode: Trivia Only")
        return trivia, "trivia"
    elif CONTENT_MODE == "slang_only":
        logger.info("💬 Mode: Slang Only")
        return slang, "slang"
    elif CONTENT_MODE == "both":
        logger.info("📚💬 Mode: Both Trivia & Slang")
        return trivia + slang, "mixed"
    else:
        logger.warning(f"❓ Unknown mode '{CONTENT_MODE}', defaulting to trivia_only")
        return trivia, "trivia"

def create_and_post(cl: Client, human_behavior: HumanBehavior):
    try:
        if human_behavior.should_take_break():
            logger.info("🔄 Resuming after break...")

        human_behavior.random_delay(60, 300)

        # Get content based on current mode
        content_pool, content_type = get_content_pool()
        
        if not content_pool:
            logger.error(f"❌ No {content_type} content available")
            return

        content = random.choice(content_pool)
        logger.info(f"📄 Selected {content_type}: {content[:50]}...")

        filename = f"post_{int(time.time())}_{random.randint(1000,9999)}.jpg"
        path = create_dark_text_post(content, filename)

        hashtag_sets = [
            "#CarnivalCompanion #Caribbean #IslandLife #Trivia",
            "#CaribbeanVibes #Carnival #IslandTrivia #Culture",
            "#LearnCaribbean #CarnivalFacts #IslandKnowledge"
        ]
        caption = f"{content}\n\n{random.choice(hashtag_sets)}"
        human_behavior.typing_delay(caption)

        try:
            human_behavior.random_delay(30, 90)
            cl.delay_range = human_behavior.get_human_like_delay_range()
            cl.photo_upload(path, caption)
            logger.info("✅ Post successful")

        except (LoginRequired, ChallengeRequired):
            logger.warning("🔄 Session expired, reconnecting...")
            if advanced_login(cl, human_behavior):
                human_behavior.random_delay(60, 120)
                cl.photo_upload(path, caption)
                logger.info("✅ Retry post successful")
            else:
                raise

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            human_behavior.random_delay(300, 600)
            raise

        human_behavior.random_delay(30, 60)
        if os.path.exists(path):
            os.remove(path)
            logger.info("🗑️ Temp file removed")

        schedule_next_post(cl, human_behavior)

    except Exception as e:
        logger.error(f"Error in posting: {e}")
        human_behavior.random_delay(300, 600)
        schedule_next_post(cl, human_behavior)

def get_random_peak_time_within_day():
    windows = [
        (8, 11),
        (12, 14),
        (16, 19),
        (20, 23)
    ]
    chosen = random.choice(windows)
    hour = random.randint(chosen[0], chosen[1] - 1)
    minute = random.randint(0, 59)
    return hour, minute

def schedule_next_post(cl: Client, human_behavior: HumanBehavior):
    times = []
    for _ in range(2):
        h, m = get_random_peak_time_within_day()
        t_str = f"{h:02d}:{m:02d}"
        times.append(t_str)

    schedule.clear()
    for t_str in times:
        try:
            schedule.every().day.at(t_str).do(lambda cl=cl, hb=human_behavior: create_and_post(cl, hb))
            logger.info(f"📅 Scheduled daily post at {t_str}")
        except Exception as e:
            logger.warning(f"Failed to schedule at {t_str}: {e}")

# ------------------------------------------------------------------------------
# Main with Enhanced Stealth - FIXED PORT CONFLICT
# ------------------------------------------------------------------------------
def main():
    logger.info(f"🚀 Starting Caribbean Meme Bot ({CONTENT_MODE.replace('_', ' ').title()} Mode)...")

    if not USERNAME or not PASSWORD:
        logger.error("❌ Missing IG credentials")
        return

    human_behavior = HumanBehavior()
    cl = Client()
    cl.delay_range = human_behavior.get_human_like_delay_range()

    if os.getenv("HTTPS_PROXY"):
        cl.set_proxy(os.getenv("HTTPS_PROXY"))
        logger.info("🔌 Using proxy")

    if not advanced_login(cl, human_behavior):
        logger.error("❌ Initial login failed")
        return

    logger.info(f"✅ Bot ready with {CONTENT_MODE} mode")
    create_and_post(cl, human_behavior)

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
            if random.random() < 0.1:
                time.sleep(random.uniform(10, 30))
        except KeyboardInterrupt:
            logger.info("⏹️ Stopped by user")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            human_behavior.random_delay(300, 600)

# ------------------------------------------------------------------------------
# Entrypoint logic: FIXED PORT CONFLICT
# ------------------------------------------------------------------------------
def start_flask_app():
    """Start Flask app on the port provided by Render"""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🌐 Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_bot():
    """Start the main bot logic"""
    time.sleep(5)  # Wait for Flask to start
    main()

if __name__ == "__main__":
    # Direct execution: start both Flask and bot
    flask_thread = Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    main()
else:
    # Gunicorn execution: start bot only (Gunicorn handles Flask)
    bot_thread = Thread(target=start_bot, daemon=True)
    bot_thread.start()