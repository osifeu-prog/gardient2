import logging
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
LAT = Histogram(
    "http_request_latency_ms",
    "HTTP request latency ms",
    ["path", "method"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2000, 5000),
)

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
