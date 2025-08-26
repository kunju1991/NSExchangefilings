import requests
import logging
import os
from telegram import Bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    logging.error("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing!")
    exit(1)

bot = Bot(token=BOT_TOKEN)

STOCKS = ["RELIANCE", "TCS", "HDFCBANK"]

# NSE requires headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/119.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive"
}


def fetch_filings(stock_symbol):
    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={stock_symbol}"
    try:
        session = requests.Session()
        # first get cookies from NSE homepage
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data or "AA" not in data:
            logging.info(f"ℹ️ No filings found for {stock_symbol}")
            return None

        latest = data["AA"][0]
        headline = latest.get("sm", "No headline")
        date = latest.get("an_dt", "")
        pdf_url = latest.get("attchmntFile", "")

        return f"📢 {stock_symbol}\n📰 {headline}\n📅 {date}\n🔗 {pdf_url}"

    except Exception as e:
        logging.error(f"Error fetching filings for {stock_symbol}: {e}")
        return None


def main():
    logging.info("🔄 Checking NSE filings (single-run mode)...")
    for stock in STOCKS:
        msg = fetch_filings(stock)
        if msg:
            bot.send_message(chat_id=CHAT_ID, text=msg)

    logging.info("🏁 Job finished. Exiting now.")


if __name__ == "__main__":
    main()
