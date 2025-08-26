import os
import logging
import time
import requests
from telegram import Bot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TELEGRAM_BOT_ID = os.getenv("TELEGRAM_BOT_ID")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STOCKS = ["RELIANCE", "TCS", "HDFCBANK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Ch-Ua": '"Chromium";v="128", "Not=A?Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

def mask_cookie(val: str) -> str:
    """Mask sensitive cookie values for safe logging."""
    if not val:
        return ""
    if len(val) <= 6:
        return "***"
    return val[:3] + "..." + val[-3:]

def make_session():
    """Create a session with retries and warm-up cookies."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[401, 403, 429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        time.sleep(1)
        session.get("https://www.nseindia.com/api/marketStatus", headers=HEADERS, timeout=10)

        # Log cookies (masked)
        cookies = {k: mask_cookie(v) for k, v in session.cookies.get_dict().items()}
        logging.info(f"🍪 Warm-up cookies acquired: {cookies}")

    except Exception as e:
        logging.warning(f"Warm-up failed: {e}")
    return session

def fetch_filings(stock_symbol, session):
    url = f"https://www.nseindia.com/api/corporate
