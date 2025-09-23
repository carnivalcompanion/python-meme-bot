# ------------------------------------------------------------------------------
# Caribbean Meme Bot (Stealth Edition)
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
# Stealth Configuration
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("caribbean_meme_bot")

# Disable instagrapi debug logging
logging.getLogger("instagrapi").setLevel(logging.WARNING)

load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

TRIVIA_FILE = "trivia.txt"
SLANG_FILE = "slang.txt"
PROFILE_IMG = "placeholder.jpg"

# ------------------------------------------------------------------------------
# Human-like Behavior Simulation
# ------------------------------------------------------------------------------
class HumanBehavior:
    def __init__(self):
        self.last_action_time = 0
        self.action_count = 0
        self.daily_limit = random.randint(2, 4)  # Vary daily limits
        
    def random_delay(self, min_sec=30, max_sec=120):
        """Random delay between actions"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        
    def typing_delay(self, text):
        """Simulate typing speed based on text length"""
        delay = len(text) * 0.1 + random.uniform(0.5, 2.0)
        time.sleep(delay)
        
    def get_human_like_delay_range(self):
        """Vary delay ranges to avoid patterns"""
        base_min = random.uniform(1.5, 3.5)
        base_max = random.uniform(4.5, 8.5)
        return [base_min, base_max]
    
    def should_take_break(self):
        """Random breaks to simulate human usage patterns"""
        self.action_count += 1
        if self.action_count % random.randint(3, 6) == 0:
            break_time = random.uniform(1800, 7200)  # 30min to 2hr break
            logger.info(f"🧘 Taking human-like break for {break_time/60:.1f} minutes")
            time.sleep(break_time)
            return True
        return False

# ------------------------------------------------------------------------------
# Advanced Session Management
# ------------------------------------------------------------------------------
def create_device_settings():
    """Generate consistent device settings"""
    devices = [
        {
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 29,
                "android_release": "10.0",
                "dpi": "480dpi",
                "resolution": "1080x1920",
                "manufacturer": "Samsung",
                "device": "SM-G973F",
                "model": "Galaxy S10",
                "cpu": "exynos9820"
            }
        },
        {
            "device_settings": {
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
        }
    ]
    return random.choice(devices)

def save_secure_session(client, username):
    """Encrypt session data before saving"""
    session_data = client.get_settings()
    session_str = json.dumps(session_data)
    
    # Simple obfuscation
    encoded = session_str.encode('utf-8')
    filename = hashlib.md5(f"{username}_{int(time.time())}".encode()).hexdigest()[:16] + ".session"
    
    with open(filename, 'wb') as f:
        f.write(encoded[::-1])  # Reverse bytes for basic obfuscation
        
    return filename

def load_secure_session(client, username):
    """Load and decrypt session data"""
    session_files = [f for f in os.listdir('.') if f.endswith('.session')]
    if not session_files:
        return None
        
    latest_file = max(session_files, key=os.path.getctime)
    
    try:
        with open(latest_file, 'rb') as f:
            encoded_data = f.read()
            
        session_str = encoded_data[::-1].decode('utf-8')  # Reverse de-obfuscation
        session_data = json.loads(session_str)
        client.set_settings(session_data)
        return True
    except Exception as e:
        logger.warning(f"Session load failed: {e}")
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
    """Advanced login with human-like behavior and challenge handling"""
    try:
        human_behavior.random_delay(10, 30)  # Delay before login
        
        # Try to load existing session first
        if load_secure_session(client, USERNAME):
            logger.info("Loaded existing session")
            human_behavior.random_delay(5, 15)
            
            # Verify session is still valid
            try:
                client.get_timeline_feed()
                logger.info("Session verified ✅")
                return True
            except (LoginRequired, ChallengeRequired):
                logger.info("Session expired, need fresh login")
                os.remove([f for f in os.listdir('.') if f.endswith('.session')][0])
        
        # Fresh login with device simulation
        device_settings = create_device_settings()
        client.set_settings(device_settings)
        
        logger.info("Performing fresh login...")
        human_behavior.typing_delay(USERNAME)
        client.login(USERNAME, PASSWORD)
        
        # Save session securely
        save_secure_session(client, USERNAME)
        logger.info("New session created and saved ✅")
        
        human_behavior.random_delay(10, 20)  # Delay after login
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
# Image Generator (Twitter-style dark post)
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
# Stealth Posting Logic
# ------------------------------------------------------------------------------
def create_and_post(cl: Client, human_behavior: HumanBehavior):
    try:
        if human_behavior.should_take_break():
            logger.info("🔄 Resuming after break...")
            
        human_behavior.random_delay(60, 300)  # Delay before starting
        
        trivia = read_content(TRIVIA_FILE)
        slang = read_content(SLANG_FILE)
        if not trivia and not slang:
            logger.error("❌ No content available")
            return

        content = random.choice(trivia + slang)
        logger.info(f"📄 Selected: {content[:50]}...")

        filename = f"post_{int(time.time())}_{random.randint(1000,9999)}.jpg"
        path = create_dark_text_post(content, filename)
        
        # Vary captions and hashtags
        hashtag_sets = [
            "#CarnivalCompanion #Caribbean #IslandLife #Trivia",
            "#CaribbeanVibes #Carnival #IslandTrivia #Culture",
            "#LearnCaribbean #CarnivalFacts #IslandKnowledge"
        ]
        
        caption = f"{content}\n\n{random.choice(hashtag_sets)}"
        human_behavior.typing_delay(caption)  # Simulate caption typing

        try:
            # Vary delay before upload
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
            # Don't immediately retry on failure
            human_behavior.random_delay(300, 600)
            raise

        # Cleanup with delay
        human_behavior.random_delay(30, 60)
        if os.path.exists(path):
            os.remove(path)
            logger.info("🗑️ Temp file removed")

        schedule_next_post(cl, human_behavior)

    except Exception as e:
        logger.error(f"Error in posting: {e}")
        human_behavior.random_delay(300, 600)  # Longer delay on error
        schedule_next_post(cl, human_behavior)

def get_random_peak_time():
    """More varied posting times"""
    now = datetime.now()
    
    # Wider time windows with more variation
    peaks = [
        (8, 11),    # Morning
        (12, 14),   # Lunch
        (16, 19),   # Evening
        (20, 23)    # Night
    ]
    
    start, end = random.choice(peaks)
    t = now.replace(
        hour=random.randint(start, end-1),
        minute=random.randint(0, 59),
        second=0, 
        microsecond=0
    )
    
    # Add random day variation (sometimes post next day, sometimes same day)
    if t <= now or random.random() < 0.3:
        t += timedelta(days=random.randint(1, 2))
        
    return t

def schedule_next_post(cl: Client, human_behavior: HumanBehavior):
    next_time = get_random_peak_time()
    delay = (next_time - datetime.now()).total_seconds()
    
    # Add some randomness to the schedule
    delay += random.uniform(-3600, 3600)  # ±1 hour variation
    
    logger.info(f"📅 Next post at {next_time} (~{delay/3600:.1f}h)")
    schedule.clear()
    schedule.every(delay).seconds.do(lambda: create_and_post(cl, human_behavior))

# ------------------------------------------------------------------------------
# Main with Enhanced Stealth
# ------------------------------------------------------------------------------
def main():
    logger.info("🚀 Starting Caribbean Meme Bot (Stealth Edition)...")
    keep_alive()

    if not USERNAME or not PASSWORD:
        logger.error("❌ Missing IG credentials")
        return

    # Initialize human behavior simulator
    human_behavior = HumanBehavior()
    
    # Configure client with stealth settings
    cl = Client()
    cl.delay_range = human_behavior.get_human_like_delay_range()
    
    # Set proxy if available (recommended for stealth)
    if os.getenv("HTTPS_PROXY"):
        cl.set_proxy(os.getenv("HTTPS_PROXY"))
        logger.info("🔌 Using proxy")

    if not advanced_login(cl, human_behavior):
        logger.error("❌ Initial login failed")
        return

    logger.info("✅ Bot ready with stealth mode")
    human_behavior.random_delay(60, 180)  # Initial delay
    create_and_post(cl, human_behavior)

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Random small delays to avoid pattern detection
            if random.random() < 0.1:  # 10% chance
                time.sleep(random.uniform(10, 30))
                
        except KeyboardInterrupt:
            logger.info("⏹️ Stopped by user")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            human_behavior.random_delay(300, 600)  # Long delay on error

if __name__ == "__main__":
    main()