import os
import logging
import requests
from datetime import datetime

# Telegram secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# BSE Scrip Codes (Reliance, TCS, HDFC Bank)
WATCHLIST = {
    "RELIANCE": "500325",
    "TCS": "532540",
    "HDFCBANK": "500180",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_bse_filings(scrip_code):
    """Fetch announcements from BSE for a given scrip code"""
    url = f"https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?strCat=-1&strPrevDate=&strScrip={scrip_code}&strSearch=P&strToDate=&strType=C"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()

def send_telegram_message(text):
    """Send message to Telegram bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": False}
    resp = requests.post(url, data=payload)
    resp.raise_for_status()

def main():
    logging.info("🔄 Checking BSE filings (single-run mode)...")

    for name, scrip_code in WATCHLIST.items():
        try:
            data = fetch_bse_filings(scrip_code)
            if not data or "Table" not in data or not data["Table"]:
                logging.info(f"No filings found for {name}")
                continue

            latest = data["Table"][0]
            subject = latest.get("NEWS_SUB", "No Title")
            date = latest.get("NEWS_DT", "")
            pdf_url = "https://www.bseindia.com" + latest.get("ATTACHMENTNAME", "")

            message = f"📢 {name} Filing ({date})\n{subject}\n{pdf_url}"
            send_telegram_message(message)
            logging.info(f"✅ Sent filing for {name}")

        except Exception as e:
            logging.error(f"Error fetching filings for {name}: {e}")

    logging.info("🏁 Job finished. Exiting now.")

if __name__ == "__main__":
    main()
