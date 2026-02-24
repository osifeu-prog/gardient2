import os
import logging
import time
import json
from urllib.parse import urlparse

import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import Conflict

from dotenv import load_dotenv
load_dotenv(".env.local")  # local only (ignored in git)

from bot.config import BOT_TOKEN, ENV, MODE, ADMIN_CHAT_ID, WEBHOOK_URL
from bot.infrastructure import init_infrastructure, runtime_report

START_TS = time.time()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

if ENV in ("prod", "production"):
    logging.getLogger("httpx").setLevel(logging.WARNING)

ASCII_BANNER = r"""
=====================================
==           SLH  GUARDIAN          ==
=====================================
"""

def is_admin(update: Update) -> bool:
    return bool(ADMIN_CHAT_ID) and str(update.effective_chat.id) == str(ADMIN_CHAT_ID)

def _uptime_s() -> int:
    return int(time.time() - START_TS)

def _git_sha() -> str:
    # Railway commonly sets these; fall back gracefully.
    return (
        os.getenv("RAILWAY_GIT_COMMIT_SHA")
        or os.getenv("GIT_COMMIT_SHA")
        or os.getenv("COMMIT_SHA")
        or ""
    )

def _mask_bool(v: str | None) -> str:
    return "SET" if v else "MISSING"

def _parse_webhook_path(url: str) -> str:
    p = urlparse(url)
    return p.path.lstrip("/") or "tg/webhook"

def _normalize_webhook_url(url: str) -> str:
    # Ensure the URL includes the webhook path.
    if not url:
        return url
    p = urlparse(url)
    if not p.path or p.path == "/":
        return url.rstrip("/") + "/tg/webhook"
    return url

async def _log_cmd(update: Update, name: str):
    try:
        u = update.effective_user
        c = update.effective_chat
        logger.info(
            "cmd=%s chat_id=%s user_id=%s username=%s",
            name,
            getattr(c, "id", None),
            getattr(u, "id", None),
            getattr(u, "username", None),
        )
    except Exception:
        logger.exception("failed to log command")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "start")
    text = (
        f"```\n{ASCII_BANNER.strip()}\n```\n"
        "SLH Guardian — Security + Ops Control\n\n"
        "ברוך הבא ל-SLH Guardian.\n"
        "מערכת לניטור תשתיות, גיבוי, ניהול תפעול, והכנה ל-SaaS מלא.\n\n"
        "פקודות:\n"
        "/status   סטטוס DB/Redis/Alembic\n"
        "/menu     תפריט\n"
        "/whoami   מי אני\n"
        "/health   מצב מערכת\n"
    )
    if is_admin(update):
        text += "\n/admin    דוח אדמין\n/vars     Vars (SET/MISSING)\n/webhook  Webhook Info\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "whoami")
    u = update.effective_user
    c = update.effective_chat
    lines = [
        "🧾 WHOAMI",
        f"user_id: {u.id if u else None}",
        f"username: @{u.username}" if u and u.username else "username: (none)",
        f"chat_id: {c.id if c else None}",
        f"chat_type: {c.type if c else None}",
        f"is_admin_chat: {is_admin(update)}",
    ]
    await update.message.reply_text("\n".join(lines))

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "menu")
    lines = [
        "🧪 תפריט בדיקות:",
        "/start",
        "/status",
        "/menu",
        "/whoami",
        "/health",
    ]
    if is_admin(update):
        lines += ["", "🔐 פקודות אדמין:", "/admin", "/vars", "/webhook"]
    await update.message.reply_text("\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "status")
    await update.message.reply_text(await runtime_report(full=is_admin(update)))

async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "health")
    sha = _git_sha()
    lines = [
        "🫀 HEALTH",
        f"ENV: {ENV}",
        f"MODE: {MODE}",
        f"uptime_s: {_uptime_s()}",
    ]
    if sha:
        lines.append(f"git_sha: {sha[:12]}")
    # Show webhook target only to admin
    if is_admin(update):
        lines.append(f"webhook_url: {_normalize_webhook_url(WEBHOOK_URL) if WEBHOOK_URL else 'MISSING'}")
    await update.message.reply_text("\n".join(lines))

async def vars_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "vars")
    if not is_admin(update):
        await update.message.reply_text("⛔ אין לך הרשאה.")
        return
    lines = [
        "🔐 VARS (SET/MISSING)",
        f"ENV: {ENV}",
        f"MODE: {MODE}",
        f"BOT_TOKEN: {_mask_bool(BOT_TOKEN)}",
        f"DATABASE_URL: {_mask_bool(os.getenv('DATABASE_URL'))}",
        f"REDIS_URL: {_mask_bool(os.getenv('REDIS_URL'))}",
        f"ADMIN_CHAT_ID: {_mask_bool(ADMIN_CHAT_ID)}",
        f"WEBHOOK_URL: {_mask_bool(WEBHOOK_URL)}",
        f"LOG_LEVEL: {_mask_bool(os.getenv('LOG_LEVEL'))}",
        f"OPENAI_API_KEY: {_mask_bool(os.getenv('OPENAI_API_KEY'))}",
    ]
    await update.message.reply_text("\n".join(lines))

async def webhook_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "webhook")
    if not is_admin(update):
        await update.message.reply_text("⛔ אין לך הרשאה.")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
        data = r.json()
        result = data.get("result", {})
        lines = [
            "🪝 WEBHOOK INFO",
            f"url: {result.get('url') or ''}",
            f"pending_update_count: {result.get('pending_update_count')}",
            f"last_error_date: {result.get('last_error_date')}",
            f"last_error_message: {result.get('last_error_message')}",
        ]
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.exception("webhook_cmd failed")
        await update.message.reply_text(f"webhook_cmd error: {type(e).__name__}")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _log_cmd(update, "admin")
    if not is_admin(update):
        await update.message.reply_text("⛔ אין לך הרשאה.")
        return
    await update.message.reply_text("🧾 BOOT/ADMIN REPORT\n\n" + await runtime_report(full=True))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    logger.exception("Unhandled error", exc_info=err)
    if isinstance(err, Conflict):
        logger.error(
            "409 Conflict: another instance is polling. Switch to webhook mode or ensure single instance."
        )

async def post_init(app):
    await init_infrastructure()
    if ADMIN_CHAT_ID:
        await app.bot.send_message(
            chat_id=int(ADMIN_CHAT_ID),
            text="🧾 BOOT/ADMIN REPORT\n\n" + await runtime_report(full=True),
        )

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
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("vars", vars_cmd))
    app.add_handler(CommandHandler("webhook", webhook_cmd))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("admin", admin_cmd))

    print("Guardian SaaS started")

    mode = (MODE or "polling").lower()

    if mode == "webhook":
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL not set for webhook mode")

        listen = "0.0.0.0"
        port = int(os.getenv("PORT", "8080"))

        # Always ensure a valid path and URL
        webhook_url = _normalize_webhook_url(WEBHOOK_URL)
        url_path = _parse_webhook_path(webhook_url)

        app.run_webhook(
            listen=listen,
            port=port,
            url_path=url_path,
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )
    else:
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
