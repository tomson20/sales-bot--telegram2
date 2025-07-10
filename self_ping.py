import os
import time
import logging
import requests
from urllib.parse import urlparse

def get_ping_url():
    url = os.getenv("SELF_PING_URL")
    if url:
        return url.rstrip("/") + "/"
    url = os.getenv("WEBHOOK_URL")
    if url:
        # Use only the root of the webhook URL
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    raise RuntimeError("SELF_PING_URL ან WEBHOOK_URL გარემოს ცვლადი არ არის განსაზღვრული!")

PING_INTERVAL = int(os.getenv("SELF_PING_INTERVAL", "300"))  # default 5 min

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

url = get_ping_url()
logging.info(f"Self-ping enabled. Target: {url} Interval: {PING_INTERVAL}s")

while True:
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            logging.info(f"Ping OK: {url}")
        else:
            logging.warning(f"Ping non-200: {resp.status_code} {url}")
    except Exception as e:
        logging.error(f"Ping error: {e}")
    time.sleep(PING_INTERVAL) 