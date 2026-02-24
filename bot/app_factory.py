import logging
import os
import time
from typing import Callable, Awaitable

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import Conflict

from bot.config import BOT_TOKEN, ENV, ADMIN_CHAT_ID, WEBHOOK_URL, MODE
from bot.infrastructure import init_infrastructure, runtime_report
from bot.telemetry import log_json, exc_to_str, update_brief

START_TS = time.time()

def _uptime_s() -> int:
    return int(time.time() - START_TS)

def _git_sha() -> str:
    return (
        os.getenv("RAILWAY_GIT_COMMIT_SHA")
        or os.getenv("GIT_COMMIT_SHA")
        or os.getenv("COMMIT_SHA")
        or ""
    )

def is_admin(update: Update) -> bool:
    return bool(ADMIN_CHAT_ID) and str(update.effective_chat.id) == str(ADMIN_CHAT_ID)

ASCII_BANNER = ""
try:
    from pathlib import Path
    ASCII_BANNER = Path("assets/banner.txt").read_text(encoding="utf-8")
except Exception:
    ASCII_BANNER = (
        "=====================================\n"
        "==           SLH  GUARDIAN          ==\n"
        "=====================================\n"
    )

def with_latency(name: str, fn: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]):
    async def _wrap(update: Update, context: ContextTypes.DEFAULT_TYPE):
        t0 = time.perf_counter()
        try:
            await fn(update, context)
            ok = True
            err = None
        except Exception as e:
            ok = False
            err = f"{type(e).__name__}: {e}"
            raise
        finally:
            dt_ms = int((time.perf_counter() - t0) * 1000)
            brief = update_brief(update)
            log_json(logging.INFO, "handler_latency", handler=name, ok=ok, dt_ms=dt_ms, **brief, error=err)
    return _wrap

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"```\n{ASCII_BANNER.strip()}\n```\n"
        "SLH Guardian ? Security + Ops Control\n\n"
        "Welcome to SLH Guardian.\n"
        "Infra monitoring, ops control, and SaaS-ready foundation.\n\n"
        "Commands:\n"
        "/status    DB/Redis/Alembic status\n"
        "/menu      menu\n"
        "/whoami    who am I\n"
        "/health    system health\n"
    )
    if is_admin(update):
        text += "\n/admin     admin report\n/vars      Vars (SET/MISSING)\n/webhook   Webhook Info\n/diag      diagnostics\n/pingdb    DB latency\n/pingredis Redis latency\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def whoami_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    lines = [
        "WHOAMI",
        f"user_id: {u.id if u else None}",
        f"username: @{u.username}" if u and u.username else "username: (none)",
        f"chat_id: {c.id if c else None}",
        f"chat_type: {c.type if c else None}",
        f"is_admin_chat: {is_admin(update)}",
    ]
    await update.message.reply_text("\n".join(lines))

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["Commands:", "/start", "/status", "/menu", "/whoami", "/health"]
    if is_admin(update):
        lines += ["", "Admin:", "/admin", "/vars", "/webhook", "/diag", "/pingdb", "/pingredis"]
    await update.message.reply_text("\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await runtime_report(full=is_admin(update)))

async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sha = _git_sha()
    lines = ["HEALTH", f"ENV: {ENV}", f"MODE: {MODE}", f"uptime_s: {_uptime_s()}"]
    if sha:
        lines.append(f"git_sha: {sha[:12]}")
    if is_admin(update):
        lines.append(f"webhook_url: {WEBHOOK_URL or 'MISSING'}")
    await update.message.reply_text("\n".join(lines))

async def vars_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? Access denied.")
        return
    def mask(v): return "SET" if v else "MISSING"
    lines = [
        "VARS (SET/MISSING)",
        f"ENV: {ENV}",
        f"MODE: {MODE}",
        f"BOT_TOKEN: {mask(BOT_TOKEN)}",
        f"DATABASE_URL: {mask(os.getenv('DATABASE_URL'))}",
        f"REDIS_URL: {mask(os.getenv('REDIS_URL'))}",
        f"ADMIN_CHAT_ID: {mask(ADMIN_CHAT_ID)}",
        f"WEBHOOK_URL: {mask(WEBHOOK_URL)}",
        f"LOG_LEVEL: {mask(os.getenv('LOG_LEVEL'))}",
        f"OPENAI_API_KEY: {mask(os.getenv('OPENAI_API_KEY'))}",
    ]
    await update.message.reply_text("\n".join(lines))

async def webhookinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? Access denied.")
        return
    import httpx
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
    data = r.json().get("result", {})
    lines = [
        "WEBHOOK INFO",
        f"url: {data.get('url') or ''}",
        f"pending_update_count: {data.get('pending_update_count')}",
        f"last_error_date: {data.get('last_error_date')}",
        f"last_error_message: {data.get('last_error_message')}",
    ]
    await update.message.reply_text("\n".join(lines))

async def diag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? Access denied.")
        return
    sha = _git_sha()
    await update.message.reply_text("\n".join([
        "DIAG",
        f"env: {ENV}",
        f"mode: {MODE}",
        f"uptime_s: {_uptime_s()}",
        f"git_sha: {(sha[:12] if sha else '(none)')}",
        f"webhook_url: {WEBHOOK_URL or 'MISSING'}",
    ]))

async def pingdb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? Access denied.")
        return
    t0 = time.perf_counter()
    ok = True
    err = None
    try:
        _ = await runtime_report(full=False)
    except Exception as e:
        ok = False
        err = f"{type(e).__name__}: {e}"
    dt = int((time.perf_counter() - t0) * 1000)
    await update.message.reply_text(f"DB ping: {'OK' if ok else 'FAIL'} ({dt} ms){'' if not err else ' | ' + err}")

async def pingredis_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? Access denied.")
        return
    t0 = time.perf_counter()
    ok = True
    err = None
    try:
        _ = await runtime_report(full=False)
    except Exception as e:
        ok = False
        err = f"{type(e).__name__}: {e}"
    dt = int((time.perf_counter() - t0) * 1000)
    await update.message.reply_text(f"Redis ping: {'OK' if ok else 'FAIL'} ({dt} ms){'' if not err else ' | ' + err}")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? Access denied.")
        return
    await update.message.reply_text("BOOT/ADMIN REPORT\n\n" + await runtime_report(full=True))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    e = context.error
    brief = update_brief(update) if isinstance(update, Update) else {}
    log_json(logging.ERROR, "bot_error", error_type=type(e).__name__, error=str(e), trace=exc_to_str(e), **brief)
    if isinstance(e, Conflict):
        log_json(logging.ERROR, "bot_conflict_409", **brief)

async def post_init(app):
    await init_infrastructure()
    if ADMIN_CHAT_ID:
        await app.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text="BOOT/ADMIN REPORT\n\n" + await runtime_report(full=True))

def build_application():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", with_latency("start", start_cmd)))
    app.add_handler(CommandHandler("menu", with_latency("menu", menu_cmd)))
    app.add_handler(CommandHandler("status", with_latency("status", status_cmd)))
    app.add_handler(CommandHandler("health", with_latency("health", health_cmd)))
    app.add_handler(CommandHandler("vars", with_latency("vars", vars_cmd)))
    app.add_handler(CommandHandler("webhook", with_latency("webhook", webhookinfo_cmd)))
    app.add_handler(CommandHandler("diag", with_latency("diag", diag_cmd)))
    app.add_handler(CommandHandler("pingdb", with_latency("pingdb", pingdb_cmd)))
    app.add_handler(CommandHandler("pingredis", with_latency("pingredis", pingredis_cmd)))
    app.add_handler(CommandHandler("whoami", with_latency("whoami", whoami_cmd)))
    app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))
    return app
