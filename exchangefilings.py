import os
import logging
import requests

# ==============================
# 🔧 Setup logging
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==============================
# 🔧 Config from secrets
# ==============================
TELEGRAM_BOT_ID = os.getenv("TELEGRAM_BOT_ID")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# NSE symbols to track
NSE_SYMBOLS = ["RELIANCE", "TCS", "HDFCBANK"]

# BSE codes (RELIANCE, TCS, HDFCBANK)
BSE_CODES = {
    "RELIANCE": "500325",
    "TCS": "532540",
    "HDFCBANK": "500180"
}

# ==============================
# 🔧 Telegram Sender
# ==============================
def send_telegram_message(message: str):
    """Send message to Telegram bot"""
    if not TELEGRAM_BOT_ID or not TELEGRAM_CHAT_ID:
        logging.error("❌ Telegram bot config missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_ID}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        logging.info("📨 Sent to Telegram")
    except Exception as e:
        logging.error(f"⚠️ Failed to send Telegram message: {e}")

# ==============================
# 🔧 NSE Fetcher (with warm-up cookies)
# ==============================
def fetch_nse_filings(symbol):
    """Fetch announcements from NSE for a given stock symbol"""
    session = requests.Session()
    # warm-up cookies
    warmup = session.get("https://www.nseindia.com", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    logging.info(f"🍪 Warm-up cookies acquired: {session.cookies.get_dict()}")

    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}",
    }
    resp = session.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()

# ==============================
# 🔧 BSE Fetcher (fixed 403 with headers)
# ==============================
def fetch_bse_filings(scrip_code):
    """Fetch announcements from BSE for a given scrip code"""
    url = f"https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?strCat=-1&strPrevDate=&strScrip={scrip_code}&strSearch=P&strToDate=&strType=C"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.bseindia.com/corporates/ann.html",
        "X-Requested-With": "XMLHttpRequest",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()

# ==============================
# 🔧 Main Execution (single run)
# ==============================
def main():
    logging.info("🔄 Checking NSE & BSE filings (single-run mode)...")

    # --- NSE ---
    for symbol in NSE_SYMBOLS:
        try:
            data = fetch_nse_filings(symbol)
            if data.get("data"):
                latest = data["data"][0]
                headline = latest.get("headline", "No headline")
                pdf_url = latest.get("pdfLink", "")
                send_telegram_message(f"📢 NSE {symbol}: {headline}\n🔗 {pdf_url}")
        except Exception as e:
            logging.error(f"Error fetching NSE filings for {symbol}: {e}")

    # --- BSE ---
    for symbol, code in BSE_CODES.items():
        try:
            data = fetch_bse_filings(code)
            if data and "Table" in data and len(data["Table"]) > 0:
                latest = data["Table"][0]
                headline = latest.get("NEWS_SUB", "No headline")
                pdf_url = latest.get("ATTACHMENTNAME", "")
                send_telegram_message(f"📢 BSE {symbol}: {headline}\n🔗 {pdf_url}")
        except Exception as e:
            logging.error(f"Error fetching BSE filings for {symbol}: {e}")

    logging.info("🏁 Job finished. Exiting now.")

if __name__ == "__main__":
    main()
