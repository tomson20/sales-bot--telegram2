import os
import time
import logging
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_bot_url():
    """Get the bot URL from environment variables"""
    bot_url = os.getenv("BOT_URL")
    if bot_url:
        return bot_url.rstrip("/")
    
    # Fallback: construct from webhook URL if available
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        parsed = urlparse(webhook_url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    raise RuntimeError("BOT_URL ან WEBHOOK_URL გარემოს ცვლადი არ არის განსაზღვრული!")

def ping_bot():
    """Ping the bot to keep it awake"""
    try:
        bot_url = get_bot_url()
        ping_url = f"{bot_url}/ping"
        
        response = requests.get(ping_url, timeout=30)
        
        if response.status_code == 200:
            logging.info(f"✅ Ping successful: {ping_url}")
            return True
        else:
            logging.warning(f"⚠️ Ping returned {response.status_code}: {ping_url}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Ping failed: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Unexpected error during ping: {e}")
        return False

def main():
    """Main pinger loop"""
    ping_interval = int(os.getenv("PING_INTERVAL", "300"))  # 5 minutes default
    
    try:
        bot_url = get_bot_url()
        logging.info(f"🤖 Bot pinger started")
        logging.info(f"🎯 Target: {bot_url}")
        logging.info(f"⏰ Interval: {ping_interval} seconds")
        logging.info(f"🔄 Starting ping loop...")
        
    except Exception as e:
        logging.error(f"❌ Failed to initialize pinger: {e}")
        return
    
    consecutive_failures = 0
    max_failures = 5
    
    while True:
        success = ping_bot()
        
        if success:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                logging.error(f"❌ Too many consecutive failures ({consecutive_failures}). Stopping pinger.")
                break
        
        time.sleep(ping_interval)

if __name__ == "__main__":
    main() 