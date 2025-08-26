import os
import logging
import requests
from telegram import Bot

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TELEGRAM_BOT_ID = os.getenv("TELEGRAM_BOT_ID")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STOCKS = ["RELIANCE", "TCS", "HDFCBANK"]

# NSE headers (pretend to be a browser)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive"
}

def fetch_filings(stock_symbol, session):
    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={stock_symbol}"
    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("corporateAnnouncmentList"):
            latest = data["corporateAnnouncmentList"][0]
            return f"📢 {stock_symbol}: {latest.get('sm_desc', 'No details')} ({latest.get('dt_tm', '')})"
        return None
    except Exception as e:
        logging.error(f"Error fetching filings for {stock_symbol}: {e}")
        return None

def send_to_telegram(message):
    if not TELEGRAM_BOT_ID or not TELEGRAM_CHAT_ID:
        logging.error("❌ Missing TELEGRAM_BOT_ID or TELEGRAM_CHAT_ID")
        return
    try:
        bot = Bot(token=TELEGRAM_BOT_ID)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

def main():
    logging.info("🔄 Checking NSE filings (single-run mode)...")

    with requests.Session() as session:
        # Warm up session to grab cookies
        try:
            session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        except Exception as e:
            logging.warning(f"Warm-up request failed: {e}")

        for stock in STOCKS:
            filing = fetch_filings(stock, session)
            if filing:
                send_to_telegram(filing)

    logging.info("🏁 Job finished. Exiting now.")

if __name__ == "__main__":
    main()
