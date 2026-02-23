import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bot.infrastructure import init_infrastructure

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

class RedactedHTTPXFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if TOKEN:
            msg = str(record.getMessage()).replace(TOKEN, "<REDACTED>")
            record.msg = msg
            record.args = ()
        return True

logging.getLogger("httpx").addFilter(RedactedHTTPXFilter())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ Guardian SaaS is running.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ System operational.")

async def post_init(app):
    await init_infrastructure()

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN not set")

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))

    print("Guardian SaaS started")
    app.run_polling()

if __name__ == "__main__":
    main()
