import json
import time
from telegram import Update
from telegram.ext import ContextTypes

from bot.infrastructure import runtime_report

async def healthz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rep = await runtime_report(full=False)
    payload = {"ok": True, "uptime_s": rep.get("uptime_s"), "git_sha": rep.get("git_sha")}
    await update.effective_message.reply_text(json.dumps(payload, ensure_ascii=False))

async def readyz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t0 = time.perf_counter()
    try:
        _ = await runtime_report(full=False)
        payload = {"ok": True, "elapsed_ms": int((time.perf_counter() - t0) * 1000)}
    except Exception as e:
        payload = {"ok": False, "error": str(e)}
    await update.effective_message.reply_text(json.dumps(payload, ensure_ascii=False))
