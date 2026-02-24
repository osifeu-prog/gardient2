import os
import logging
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import Conflict

from bot.config import BOT_TOKEN, ENV, MODE, ADMIN_CHAT_ID, WEBHOOK_URL
from bot.infrastructure import init_infrastructure, runtime_report

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

if ENV in ("prod", "production"):
    logging.getLogger("httpx").setLevel(logging.WARNING)

ASCII_BANNER = r"""
███████╗██╗     ██╗  ██╗
██╔════╝██║     ██║  ██║
███████╗██║     ███████║
╚════██║██║     ██╔══██║
███████║███████╗██║  ██║
╚══════╝╚══════╝╚═╝  ╚═╝
"""

def is_admin(update: Update) -> bool:
    return bool(ADMIN_CHAT_ID) and str(update.effective_chat.id) == str(ADMIN_CHAT_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"```\n{ASCII_BANNER}\n```\n"
        "SLH Guardian — Security + Ops Control\n\n"
        "ברוך הבא ל-SLH Guardian.\n"
        "מערכת לניטור תשתיות, אבטחה, ניהול תפעול, והכנה ל-SaaS מלא.\n\n"
        "פקודות:\n"
        "/status  סטטוס DB/Redis/Alembic\n"
        "/menu    תפריט\n"
        "/whoami  מי אני\n"
    )
    if is_admin(update):
        text += "\n/admin  דוח אדמין\n"
    await update.message.reply_text(text, parse_mode="Markdown")
async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    lines = [
        "ًں‘¤ WHOAMI",
        f"user_id: {u.id if u else None}",
        f"username: @{u.username}" if u and u.username else "username: (none)",
        f"chat_id: {c.id if c else None}",
        f"chat_type: {c.type if c else None}",
        f"is_admin_chat: {is_admin(update)}",
    ]
    await update.message.reply_text("\n".join(lines))

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [
        "ًں§­ ×ھ×¤×¨×™×ک ×¤×§×•×“×•×ھ:",
        "/start",
        "/status",
        "/menu",
        "/whoami",
    ]
    if is_admin(update):
        lines += ["", "ًں›  ×گ×“×‍×™×ں:", "/admin"]
    await update.message.reply_text("\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await runtime_report(full=is_admin(update)))

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("â›” ×گ×™×ں ×”×¨×©×گ×”.")
        return
    await update.message.reply_text("ًںڑ€ BOOT/ADMIN REPORT\n\n" + await runtime_report(full=True))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    logging.getLogger(__name__).exception("Unhandled error", exc_info=err)
    if isinstance(err, Conflict):
        logging.getLogger(__name__).error(
            "409 Conflict: another instance is polling. Switch to webhook mode or ensure single instance."
        )

async def post_init(app):
    await init_infrastructure()
    if ADMIN_CHAT_ID:
        await app.bot.send_message(
            chat_id=int(ADMIN_CHAT_ID),
            text="ًںڑ€ BOOT/ADMIN REPORT\n\n" + await runtime_report(full=True),
        )

def _parse_webhook_path(url: str) -> str:
    p = urlparse(url)
    return p.path.lstrip("/") or "tg/webhook"

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
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("admin", admin_cmd))

    print("Guardian SaaS started")

    mode = (MODE or "polling").lower()

    if mode == "webhook":
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL not set for webhook mode")

        listen = "0.0.0.0"
        port = int(os.getenv("PORT", "8080"))
        url_path = _parse_webhook_path(WEBHOOK_URL)

        app.run_webhook(
            listen=listen,
            port=port,
            url_path=url_path,
            webhook_url=WEBHOOK_URL,
            drop_pending_updates=True,
        )
    else:
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()