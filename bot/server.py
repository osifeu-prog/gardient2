
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

import asyncio

async def _measure_readyz():
    """
    Returns (ok, payload)
    payload includes db_ms, redis_ms, errors if any.
    """
    payload = {"ok": True}
    t0 = time.perf_counter()
    db_ok = True
    db_err = None
    try:
        from bot.infrastructure import check_postgres
        await check_postgres()
    except Exception as e:
        db_ok = False
        db_err = f"{type(e).__name__}: {e}"
    payload["db_ok"] = db_ok
    payload["db_ms"] = int((time.perf_counter() - t0) * 1000)
    if db_err:
        payload["db_error"] = db_err
        payload["ok"] = False

    t1 = time.perf_counter()
    r_ok = True
    r_err = None
    try:
        from bot.infrastructure import check_redis
        await check_redis()
    except Exception as e:
        r_ok = False
        r_err = f"{type(e).__name__}: {e}"
    payload["redis_ok"] = r_ok
    payload["redis_ms"] = int((time.perf_counter() - t1) * 1000)
    if r_err:
        payload["redis_error"] = r_err
        payload["ok"] = False

    return payload["ok"], payload


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
        await init_infrastructure()
            await ptb_app.initialize()
        await ptb_app.start()
        log_json(logging.INFO, "fastapi_startup", uptime_s=uptime_s(), git_sha=(git_sha()[:12] if git_sha() else None))
    try:
        yield
    finally:
        print("LIFESPAN: shutting down", flush=True)
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
    ok, payload = await _measure_readyz()
    if ok:
        return payload
    return JSONResponse(payload, status_code=503)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.post("/tg/webhook")
async def tg_webhook(request: Request):
    payload = await request.json()
    update = Update.de_json(payload, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"ok": True}
