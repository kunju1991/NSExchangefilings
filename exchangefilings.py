import os
import logging
import requests
from telegram import Bot

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Read secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing!")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# NSE headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

# Stocks to track
STOCK_SYMBOLS = ["RELIANCE", "TCS", "HDFCBANK"]


def fetch_announcements(stock_symbol: str):
    """Fetch latest corporate announcement for a given stock."""
    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={stock_symbol}"

    try:
        with requests.Session() as s:
            s.headers.update(HEADERS)

            # Get cookies first
            s.get("https://www.nseindia.com", timeout=10)

            # Then hit API
            resp = s.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            announcements = data.get("corporateAnnouncements", [])
            if not announcements:
                logging.info(f"ℹ️ No announcements for {stock_symbol}")
                return None

            latest = announcements[0]
            subject = latest.get("subject", "No subject")
            date = latest.get("date", "Unknown date")
            pdf_url = latest.get("pdfLink", "")

            message = f"📢 {stock_symbol} filing ({date}):\n{subject}"
            if pdf_url:
                message += f"\n🔗 {pdf_url}"

            return message

    except Exception as e:
        logging.error(f"Error fetching filings for {stock_symbol}: {e}")
        return None


def main():
    logging.info("🔄 Checking NSE filings (single-run mode)...")

    for symbol in STOCK_SYMBOLS:
        msg = fetch_announcements(symbol)
        if msg:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

    logging.info("🏁 Job finished. Exiting now.")


if __name__ == "__main__":
    main()
