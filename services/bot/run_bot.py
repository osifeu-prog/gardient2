
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Guardian Enterprise Bot is live.")

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot OK.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health))
    app.run_polling()

if __name__ == "__main__":
    main()
