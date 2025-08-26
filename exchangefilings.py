import os
import requests
import logging
from telegram import Bot

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Environment variables from GitHub Secrets ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN:
    logging.error("❌ TELEGRAM_BOT_TOKEN is missing! Set it as a GitHub Secret.")
    exit(1)

if not TELEGRAM_CHAT_ID:
    logging.error("❌ TELEGRAM_CHAT_ID is missing! Set it as a GitHub Secret.")
    exit(1)

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Example function to check filings
def check_filings(stock_symbol="RELIANCE"):
    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={stock_symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data or "corporateAnnouncements" not in data:
            logging.warning(f"No announcements found for {stock_symbol}")
            return

        # Take only latest announcement (you can expand logic here)
        latest = data["corporateAnnouncements"][0]
        msg = f"📢 {stock_symbol} filing:\n{latest.get('subject', 'No subject')}"
        logging.info(f"Sending to Telegram: {msg}")

        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

    except Exception as e:
        logging.error(f"Error fetching filings for {stock_symbol}: {e}")

def main():
    logging.info("🔄 Checking NSE filings (single-run mode)...")
    check_filings("RELIANCE")   # Example, add more tickers as needed
    logging.info("🏁 Job finished. Exiting now.")

if __name__ == "__main__":
    main()
