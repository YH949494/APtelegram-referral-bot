import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# === Flask App (for UptimeRobot) ===
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)


# === Telegram Bot Logic ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    if message.photo or message.video:
        caption = message.caption or ""
        if caption.lower().startswith("#mywin"):
            return  # Do not delete valid posts
    try:
        await message.delete()
    except Exception as e:
        print(f"Failed to delete message: {e}")

def run_telegram():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN is missing!")
        return

    print("✅ Starting Telegram bot...")
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()

    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.ALL, handle_message))

    app_telegram.run_polling()

# === Start Flask + Telegram ===
if __name__ == "__main__":
    Thread(target=run_flask).start()
    run_telegram()
