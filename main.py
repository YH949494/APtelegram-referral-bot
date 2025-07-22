import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)

# Route for Fly.io health check (UptimeRobot)
@app.route("/")
def home():
    return "Bot is alive!"

# Define Telegram bot logic
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    if message.photo or message.video:
        caption = message.caption or ""
        if caption.lower().startswith("#mywin"):
            return  # Keep the message
    try:
        await message.delete()
    except Exception as e:
        print(f"Failed to delete message: {e}")

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

def run_telegram():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    handler = MessageHandler(filters.ALL, handle_message)
    app_telegram.add_handler(handler)
    app_telegram.run_polling()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    run_telegram()
