import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from telegram import Update

from bot.app_factory import build_application
from bot.infrastructure import init_infrastructure
from bot.telemetry import log_json, exc_to_str

APP_START = time.time()

REGISTRY = CollectorRegistry()

REQS = Counter(
    "http_requests_total",
    "HTTP requests total",
    ["path", "method", "status"],
    registry=REGISTRY,
)
LAT = Histogram(
    "http_request_latency_ms",
    "HTTP request latency ms",
    ["path", "method"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2000, 5000),
    registry=REGISTRY,
)


BOT_CMDS = Counter(
    "bot_commands_total",
    "Bot commands total",
    ["cmd"],
    registry=REGISTRY,
)

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

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Infra first
    await init_infrastructure()
    # Telegram bot init/start
    await ptb_app.initialize()
    await ptb_app.start()
    log_json(
        logging.INFO,
        "fastapi_startup",
        uptime_s=uptime_s(),
        git_sha=(git_sha()[:12] if git_sha() else None),
    )
    try:
        yield
    finally:
        await ptb_app.stop()
        await ptb_app.shutdown()
        log_json(logging.INFO, "fastapi_shutdown")

app = FastAPI(lifespan=lifespan)

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
        log_json(
            logging.ERROR,
            "http_error",
            path=path,
            method=method,
            error_type=type(e).__name__,
            error=str(e),
            trace=exc_to_str(e),
        )
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
    t0 = time.perf_counter()
    try:
        from bot.infrastructure import runtime_report
        _ = await runtime_report(full=False)
        return {"ok": True, "elapsed_ms": int((time.perf_counter() - t0) * 1000)}
    except Exception as e:
        return JSONResponse(
            {"ok": False, "elapsed_ms": int((time.perf_counter() - t0) * 1000), "error": f"{type(e).__name__}: {e}"},
            status_code=503,
        )


@app.get("/snapshot")
async def snapshot():
    # lightweight JSON snapshot for ops
    return {
        "ok": True,
        "healthz": await healthz(),
        "version": await version(),
        "readyz": await readyz(),
    }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.post("/tg/webhook")
async def tg_webhook(request: Request):
    payload = await request.json()
    # Count /commands from Telegram updates (best-effort)
    try:
        msg = payload.get("message") or payload.get("edited_message") or {}
        text = (msg.get("text") or "").strip()
        if text.startswith("/"):
            cmd = text.split()[0].split("@")[0].lstrip("/")
            if cmd:
                BOT_CMDS.labels(cmd=cmd).inc()
    except Exception:
        pass

    update = Update.de_json(payload, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"ok": True}
