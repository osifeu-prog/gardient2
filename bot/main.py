import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import Conflict

from bot.config import BOT_TOKEN, ENV, MODE, ADMIN_CHAT_ID
from bot.infrastructure import init_infrastructure, runtime_report

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# reduce noise in production
if ENV in ("prod", "production"):
    logging.getLogger("httpx").setLevel(logging.WARNING)

ASCII_BANNER = r"""
  ____  _     _   _
 / ___|| |   | | | |
 \___ \| |   | |_| |
  ___) | |___|  _  |
 |____/|_____|_| |_|

SLH Guardian — Security + Ops Control
"""

def is_admin(update: Update) -> bool:
    return bool(ADMIN_CHAT_ID) and str(update.effective_chat.id) == str(ADMIN_CHAT_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{ASCII_BANNER}\n"
        "ברוך הבא ל-SLH Guardian.\n"
        "מערכת לניטור תשתיות, אבטחה, ניהול תפעול, והכנה ל-SaaS מלא.\n\n"
        "פקודות:\n"
        "/status  סטטוס DB/Redis/Alembic\n"
        "/menu  תפריט\n"
    )
    if is_admin(update):
        text += "\n/admin  דוח אדמין\n"
    await update.message.reply_text(text)

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [
        "🧭 תפריט פקודות:",
        "/start",
        "/status",
        "/menu",
    ]
    if is_admin(update):
        lines += ["", "🛠 אדמין:", "/admin"]
    await update.message.reply_text("\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await runtime_report(full=is_admin(update)))

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ אין הרשאות אדמין.")
        return
    await update.message.reply_text("🚀 BOOT/ADMIN REPORT\n\n" + await runtime_report(full=True))


async def whoami_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update.effective_chat else None
    user_id = update.effective_user.id if update.effective_user else None
    username = update.effective_user.username if update.effective_user else None
    await update.message.reply_text(
        "👤 whoami\n"
        f"chat_id: {chat_id}\n"
        f"user_id: {user_id}\n"
        f"username: @{username}\n"
        f"is_admin: {is_admin(update)}"
    )
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    logging.getLogger(__name__).exception("Unhandled error", exc_info=err)
    if isinstance(err, Conflict):
        logging.getLogger(__name__).error("409 Conflict: another instance is polling. Ensure only one instance OR switch to webhook mode.")

async def post_init(app):
    await init_infrastructure()
    if ADMIN_CHAT_ID:
        await app.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text="🚀 BOOT REPORT\n\n" + await runtime_report(full=True))

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))

    print("Guardian SaaS started")

    # keep polling for now; later we can add webhook mode
    app.run_polling()

if __name__ == "__main__":
    main()

