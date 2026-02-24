from pathlib import Path

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    content = content.replace("\r\n", "\n")
    p.write_text(content, encoding="utf-8", newline="\n")

write("bot/telemetry.py", """import json
import logging
import time
import traceback
from typing import Any, Dict

LOGGER_NAME = "guardian"
logger = logging.getLogger(LOGGER_NAME)

def now_ms() -> int:
    return int(time.time() * 1000)

def log_json(level: int, event: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {"ts_ms": now_ms(), "event": event, **fields}
    msg = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    logger.log(level, msg)

def exc_to_str(e: BaseException) -> str:
    return "".join(traceback.format_exception(type(e), e, e.__traceback__)).strip()

def update_brief(update: Any) -> Dict[str, Any]:
    try:
        u = getattr(update, "effective_user", None)
        c = getattr(update, "effective_chat", None)
        m = getattr(update, "effective_message", None)
        txt = getattr(m, "text", None) if m else None
        return {
            "chat_id": getattr(c, "id", None),
            "user_id": getattr(u, "id", None),
            "username": getattr(u, "username", None),
            "text": (txt[:120] if isinstance(txt, str) else None),
        }
    except Exception:
        return {}
""")

write("bot/app_factory.py", """import logging
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
        "=====================================\\n"
        "==           SLH  GUARDIAN          ==\\n"
        "=====================================\\n"
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
        f"```\\n{ASCII_BANNER.strip()}\\n```\\n"
        "SLH Guardian ? Security + Ops Control\\n\\n"
        "???? ??? ?-SLH Guardian.\\n"
        "????? ?????? ??????, ?????, ????? ?????, ????? ?-SaaS ???.\\n\\n"
        "??????:\\n"
        "/status    ????? DB/Redis/Alembic\\n"
        "/menu      ?????\\n"
        "/whoami    ?? ???\\n"
        "/health    ??? ?????\\n"
    )
    if is_admin(update):
        text += "\\n/admin     ??? ?????\\n/vars      Vars (SET/MISSING)\\n/webhook   Webhook Info\\n/diag      ???????????\\n/pingdb    ????? DB latency\\n/pingredis ????? Redis latency\\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def whoami_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    lines = [
        "?? WHOAMI",
        f"user_id: {u.id if u else None}",
        f"username: @{u.username}" if u and u.username else "username: (none)",
        f"chat_id: {c.id if c else None}",
        f"chat_type: {c.type if c else None}",
        f"is_admin_chat: {is_admin(update)}",
    ]
    await update.message.reply_text("\\n".join(lines))

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["?? ????? ??????:", "/start", "/status", "/menu", "/whoami", "/health"]
    if is_admin(update):
        lines += ["", "?? ?????? ?????:", "/admin", "/vars", "/webhook", "/diag", "/pingdb", "/pingredis"]
    await update.message.reply_text("\\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await runtime_report(full=is_admin(update)))

async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sha = _git_sha()
    lines = ["?? HEALTH", f"ENV: {ENV}", f"MODE: {MODE}", f"uptime_s: {_uptime_s()}"]
    if sha:
        lines.append(f"git_sha: {sha[:12]}")
    if is_admin(update):
        lines.append(f"webhook_url: {WEBHOOK_URL or 'MISSING'}")
    await update.message.reply_text("\\n".join(lines))

async def vars_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? ??? ?? ?????.")
        return
    def mask(v): return "SET" if v else "MISSING"
    lines = [
        "?? VARS (SET/MISSING)",
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
    await update.message.reply_text("\\n".join(lines))

async def webhookinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? ??? ?? ?????.")
        return
    import httpx
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
    data = r.json().get("result", {})
    lines = [
        "?? WEBHOOK INFO",
        f"url: {data.get('url') or ''}",
        f"pending_update_count: {data.get('pending_update_count')}",
        f"last_error_date: {data.get('last_error_date')}",
        f"last_error_message: {data.get('last_error_message')}",
    ]
    await update.message.reply_text("\\n".join(lines))

async def diag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? ??? ?? ?????.")
        return
    sha = _git_sha()
    await update.message.reply_text("\\n".join([
        "?? DIAG",
        f"env: {ENV}",
        f"mode: {MODE}",
        f"uptime_s: {_uptime_s()}",
        f"git_sha: {(sha[:12] if sha else '(none)')}",
        f"webhook_url: {WEBHOOK_URL or 'MISSING'}",
    ]))

async def pingdb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? ??? ?? ?????.")
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
    await update.message.reply_text(f"??? DB ping: {'OK' if ok else 'FAIL'} ({dt} ms){'' if not err else ' | ' + err}")

async def pingredis_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? ??? ?? ?????.")
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
    await update.message.reply_text(f"?? Redis ping: {'OK' if ok else 'FAIL'} ({dt} ms){'' if not err else ' | ' + err}")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? ??? ?? ?????.")
        return
    await update.message.reply_text("?? BOOT/ADMIN REPORT\\n\\n" + await runtime_report(full=True))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    e = context.error
    brief = update_brief(update) if isinstance(update, Update) else {}
    log_json(logging.ERROR, "bot_error", error_type=type(e).__name__, error=str(e), trace=exc_to_str(e), **brief)
    if isinstance(e, Conflict):
        log_json(logging.ERROR, "bot_conflict_409", **brief)

async def post_init(app):
    await init_infrastructure()
    if ADMIN_CHAT_ID:
        await app.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text="?? BOOT/ADMIN REPORT\\n\\n" + await runtime_report(full=True))

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
""")

write("bot/server.py", """import logging
import os
import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from telegram import Update

from bot.app_factory import build_application
from bot.telemetry import log_json, exc_to_str

APP_START = time.time()

REQS = Counter("http_requests_total", "HTTP requests total", ["path", "method", "status"])
LAT = Histogram("http_request_latency_ms", "HTTP request latency ms", ["path", "method"], buckets=(5,10,25,50,100,250,500,1000,2000,5000))

app = FastAPI()
ptb_app = build_application()

def uptime_s() -> int:
    return int(time.time() - APP_START)

def git_sha() -> str:
    return (
        os.getenv("RAILWAY_GIT_COMMIT_SHA")
        or os.getenv("GIT_COMMIT_SHA")
        or os.getenv("COMMIT_SHA")
        or ""
    )

@app.on_event("startup")
async def _startup():
    await ptb_app.initialize()
    await ptb_app.start()
    log_json(logging.INFO, "fastapi_startup", uptime_s=uptime_s(), git_sha=(git_sha()[:12] if git_sha() else None))

@app.on_event("shutdown")
async def _shutdown():
    await ptb_app.stop()
    await ptb_app.shutdown()
    log_json(logging.INFO, "fastapi_shutdown")

@app.middleware("http")
async def _mw(request: Request, call_next):
    t0 = time.perf_counter()
    path = request.url.path
    method = request.method
    status = 500
    try:
        resp = await call_next(request)
        status = resp.status_code
        return resp
    except Exception as e:
        log_json(logging.ERROR, "http_error", path=path, method=method, error_type=type(e).__name__, error=str(e), trace=exc_to_str(e))
        return JSONResponse({"ok": False, "error": type(e).__name__}, status_code=500)
    finally:
        dt_ms = int((time.perf_counter() - t0) * 1000)
        LAT.labels(path=path, method=method).observe(dt_ms)
        REQS.labels(path=path, method=method, status=str(status)).inc()
        log_json(logging.INFO, "http_access", path=path, method=method, status=status, dt_ms=dt_ms)

@app.get("/healthz")
async def healthz():
    return {"ok": True, "uptime_s": uptime_s(), "git_sha": (git_sha()[:12] if git_sha() else None)}

@app.get("/version")
async def version():
    return {"service": "gardient2", "git_sha": git_sha(), "uptime_s": uptime_s()}

@app.get("/readyz")
async def readyz():
    try:
        from bot.infrastructure import runtime_report
        _ = await runtime_report(full=False)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"{type(e).__name__}: {e}"}, status_code=503)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/tg/webhook")
async def tg_webhook(request: Request):
    payload = await request.json()
    update = Update.de_json(payload, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"ok": True}

def main():
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("bot.server:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
""")

print("OK: wrote FastAPI files")
