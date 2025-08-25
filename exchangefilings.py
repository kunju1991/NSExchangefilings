import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ------------------ Logging ------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),   # save logs to file
        logging.StreamHandler()           # also print to console
    ]
)
logger = logging.getLogger(__name__)

# ------------------ Bot Token ------------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment!")
    raise ValueError("TELEGRAM_BOT_TOKEN must be set as an environment variable")

# ------------------ User Data ------------------
USERS_FILE = "users.json"

def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {USERS_FILE}: {e}")
    return {}

def save_users(users):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save {USERS_FILE}: {e}")

users = load_users()

# ------------------ NSE Filing Fetch ------------------
def get_latest_filings(stock_symbol):
    url = f"https://www.nseindia.com/api/corporate-announcements?symbol={stock_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "rows" in data and data["rows"]:
            latest = data["rows"][0]
            return f"📢 {stock_symbol} filing: {latest.get('desc', 'No desc')} ({latest.get('dt', '')})"
        return f"No filings found for {stock_symbol}"
    except Exception as e:
        logger.error(f"Error fetching NSE filings for {stock_symbol}: {e}")
        return f"❌ Error fetching NSE filings for {stock_symbol}"

# ------------------ Bot Commands ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    if user_id not in users:
        users[user_id] = {"stocks": []}
        save_users(users)
    await update.message.reply_text("👋 Welcome! Use /add <STOCK> to track filings, /list to see your stocks.")

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /add RELIANCE")
        return
    stock = context.args[0].upper()
    users.setdefault(user_id, {"stocks": []})
    if stock not in users[user_id]["stocks"]:
        users[user_id]["stocks"].append(stock)
        save_users(users)
        await update.message.reply_text(f"✅ Added {stock} to your watchlist.")
    else:
        await update.message.reply_text(f"ℹ️ {stock} is already in your list.")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    stocks = users.get(user_id, {}).get("stocks", [])
    if stocks:
        await update.message.reply_text("📌 Your watchlist: " + ", ".join(stocks))
    else:
        await update.message.reply_text("❌ You are not tracking any stocks. Use /add <STOCK>.")

async def filings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    stocks = users.get(user_id, {}).get("stocks", [])
    if not stocks:
        await update.message.reply_text("❌ No stocks in your watchlist. Use /add <STOCK>.")
        return
    for stock in stocks:
        filing_msg = get_latest_filings(stock)
        await update.message.reply_text(filing_msg)

# ------------------ Main ------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("filings", filings))

    logger.info("🤖 Bot started successfully")
    app.run_polling()

if __name__ == "__main__":
    main()
