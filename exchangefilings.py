import requests # type: ignore
import json
import os

# === Config ===
NSE_URL = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/"
}

BOT_TOKEN = os.getenv("8372701249:AAFbzxUMHM_IXFJttgp_0vepx1h24CbuLF0")
DATA_FILE = "users.json"   # stores each user's stocks + last seen filings


# === Helpers ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def fetch_filings(symbol):
    s = requests.Session()
    s.headers.update(HEADERS)
    resp = s.get(NSE_URL.format(symbol=symbol), timeout=10)
    resp.raise_for_status()
    return resp.json().get("announcements", [])

def send_to_telegram(chat_id, msg):
    url = f"https://api.telegram.org/bot{8372701249:AAFbzxUMHM_IXFJttgp_0vepx1h24CbuLF0}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=data)

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{8372701249:AAFbzxUMHM_IXFJttgp_0vepx1h24CbuLF0}/getUpdates"
    params = {"offset": offset, "timeout": 5}
    resp = requests.get(url, params=params).json()
    return resp.get("result", [])


# === Command Handling ===
def handle_commands(data, updates):
    new_offset = None
    for upd in updates:
        new_offset = upd["update_id"] + 1
        if "message" not in upd:
            continue

        chat_id = str(upd["message"]["chat"]["id"])
        msg = upd["message"].get("text", "").strip().upper()

        # Ensure private chat only
        if upd["message"]["chat"]["type"] != "private":
            continue

        if chat_id not in data:
            data[chat_id] = {"stocks": ["RELIANCE"], "last_filings": {}}
            send_to_telegram(chat_id, "👋 Welcome! Monitoring started for RELIANCE. Use /add STOCK to track more.")

        if msg.startswith("/ADD "):
            sym = msg.split()[1]
            if sym not in data[chat_id]["stocks"]:
                data[chat_id]["stocks"].append(sym)
                send_to_telegram(chat_id, f"✅ Added {sym} to your monitoring list")

        elif msg.startswith("/REMOVE "):
            sym = msg.split()[1]
            if sym in data[chat_id]["stocks"]:
                data[chat_id]["stocks"].remove(sym)
                send_to_telegram(chat_id, f"❌ Removed {sym} from your monitoring list")

        elif msg == "/LIST":
            send_to_telegram(chat_id, "📊 You are monitoring: " + ", ".join(data[chat_id]["stocks"]))

    return data, new_offset


# === Main Logic ===
def main():
    data = load_data()
    offset = None

    # Process commands
    updates = get_updates(offset)
    data, new_offset = handle_commands(data, updates)

    # Check new filings for each user
    for chat_id, user in data.items():
        for symbol in user["stocks"]:
            current = fetch_filings(symbol)
            prev = user["last_filings"].get(symbol, [])

            new_filings = [f for f in current if f["slug"] not in prev]

            for f in new_filings:
                msg = (
                    f"<b>{f['sm_symbol']}</b> - {f['headline']}\n"
                    f"Date: {f['ann_date']}\n"
                    f"{f['pdfLink']}"
                )
                send_to_telegram(chat_id, msg)

            # update state
            user["last_filings"][symbol] = [f["slug"] for f in current]

    save_data(data)


if __name__ == "__main__":
    main()
