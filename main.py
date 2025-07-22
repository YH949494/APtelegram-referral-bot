import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)
from pymongo import MongoClient

# Load environment variables
BOT_TOKEN = os.environ["BOT_TOKEN"]
MONGODB_URI = os.environ["MONGODB_URI"]

# Connect to MongoDB
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["referral_bot"]
users_collection = db["users"]

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    referred_by = args[0] if args else None
    user_id = str(user.id)

    # Check if user already in DB
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "username": user.username,
            "referred_by": referred_by,
            "referrals": 0
        })

        # If they were referred, add to the referrer's count
        if referred_by:
            users_collection.update_one(
                {"user_id": referred_by},
                {"$inc": {"referrals": 1}}
            )

    await update.message.reply_text(
        f"Welcome {user.first_name}! 🎉\n"
        f"Share your referral link:\n"
        f"https://t.me/{context.bot.username}?start={user_id}"
    )

# /stats command handler
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = users_collection.find_one({"user_id": user_id})

    if user_data:
        await update.message.reply_text(
            f"You've invited {user_data.get('referrals', 0)} friend(s)!"
        )
    else:
        await update.message.reply_text("You are not registered yet. Use /start first.")

# Initialize bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))

    print("Bot running...")
    app.run_polling()
