import os
import json
import logging
import sys
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==============================
# Logging Setup (10–20 lines max per run)
# ==============================
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ==============================
# Config & Storage
# ==============================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is missing! Set it as a GitHub Secret.")
    sys.exit(1)
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

users = load_users()

# ==============================
# NSE Filing API Helper
# ==============================
def fetch_filings(stock_symbol):
    """
    Fetch NSE corporate filings for a given stock.
    For demo, we use NSE announcements API.
    """
    url = f"https://www.nseindia.com/api/corporate-announcements?symbol={stock_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        logger.error(f"❌ Failed to fetch filings for {stock_symbol}: {e}")
        return []

# ==============================
# Bot Commands
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in users:
        users[chat_id] = {"stocks": []}
        save_users(users)
    await update.message.reply_text(
        "👋 Welcome! Use /add <SYMBOL> to track a stock (e.g. /add TCS).\n"
        "Use /list to see tracked stocks.\n"
        "Use /remove <SYMBOL> to stop tracking."
    )

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Usage: /add <SYMBOL>")
        return
    symbol = context.args[0].upper()
    users.setdefault(chat_id, {"stocks": []})
    if symbol not in users[chat_id]["stocks"]:
        users[chat_id]["stocks"].append(symbol)
        save_users(users)
        await update.message.reply_text(f"✅ Added {symbol} to your watchlist.")
    else:
        await update.message.reply_text(f"ℹ️ {symbol} is already in your list.")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    stocks = users.get(chat_id, {}).get("stocks", [])
    if stocks:
        await update.message.reply_text("📊 Your watchlist: " + ", ".join(stocks))
    else:
        await update.message.reply_text("⚠️ Your watchlist is empty. Add stocks with /add <SYMBOL>.")

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Usage: /remove <SYMBOL>")
        return
    symbol = context.args[0].upper()
    if chat_id in users and symbol in users[chat_id]["stocks"]:
        users[chat_id]["stocks"].remove(symbol)
        save_users(users)
        await update.message.reply_text(f"🗑 Removed {symbol} from your watchlist.")
    else:
        await update.message.reply_text(f"⚠️ {symbol} not found in your list.")

# ==============================
# Scheduled Job
# ==============================
async def check_filings(context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔄 Bot started job cycle")
    for chat_id, data in users.items():
        stocks = data.get("stocks", [])
        if not stocks:
            continue
        logger.info(f"📊 Monitoring {len(stocks)} stocks for user {chat_id}")
        updates = []
        for stock in stocks:
            filings = fetch_filings(stock)
            if filings:
                latest = filings[0]
                msg = f"{stock}: {latest.get('sm_desc', 'New Filing')} ({latest.get('an_dt', '')})"
                updates.append(msg)
                logger.info(f"✅ {msg}")
        if updates:
            await context.bot.send_message(chat_id=chat_id, text="\n".join(updates))
        else:
            logger.info(f"ℹ️ No updates for {', '.join(stocks)}")
    logger.info("🏁 Bot finished job cycle")

# ==============================
# Main
# ==============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("remove", remove_stock))

    # Run every 5 minutes
    app.job_queue.run_repeating(check_filings, interval=300, first=5)

    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

