import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)
import pymongo

# Environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGODB_URI = os.environ.get("MONGODB_URI")
PORT = int(os.environ.get("PORT", 8080))

# Flask app for Fly.io
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is alive!"

# MongoDB setup
client = pymongo.MongoClient(MONGODB_URI)
db = client["referral_bot"]
users_col = db["users"]

# Telegram bot logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referrer_id = args[0] if args else None
    user_id = user.id
    username = user.username or user.first_name

    # Check if user exists
    existing = users_col.find_one({"user_id": user_id})
    if not existing:
        users_col.insert_one({
            "user_id": user_id,
            "username": username,
            "referrer": int(referrer_id) if referrer_id else None,
            "referrals": 0,
            "joined": True
        })
        if referrer_id:
            users_col.update_one({"user_id": int(referrer_id)}, {"$inc": {"referrals": 1}})

    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(
        f"👋 Hello {username}!\n\n"
        f"Here is your unique referral link:\n{referral_link}\n\n"
        "Share this link and earn rewards when your friends join!"
    )

async def show_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users_col.find_one({"user_id": user_id})
    count = user.get("referrals", 0) if user else 0
    await update.message.reply_text(f"📊 You have invited {count} user(s).")

async def track_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    user_id = member.from_user.id
    if member.new_chat_member.status == "member":
        users_col.update_one({"user_id": user_id}, {"$set": {"joined": True}})
    elif member.new_chat_member.status in ["left", "kicked"]:
        users_col.update_one({"user_id": user_id}, {"$set": {"joined": False}})

# Optional content filter (e.g. for #mywin bot)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    if message.photo or message.video:
        caption = message.caption or ""
        if caption.lower().startswith("#mywin"):
            return
    try:
        await message.delete()
    except Exception as e:
        print(f"Failed to delete message: {e}")

# Run Flask
def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# Run Telegram
def run_telegram():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("referrals", show_referrals))
    app_telegram.add_handler(ChatMemberHandler(track_join))
    app_telegram.add_handler(MessageHandler(filters.ALL, handle_message))  # Optional
    app_telegram.run_polling()

# Start both
if __name__ == "__main__":
    Thread(target=run_flask).start()
    run_telegram()
