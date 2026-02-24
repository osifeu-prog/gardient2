from pathlib import Path
import re

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# inject helper function block only once
if "def _measure_readyz" not in s:
    insert = '''
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
'''
    # place after imports block: after "from bot.telemetry import ..."
    anchor = "from bot.telemetry import log_json, exc_to_str"
    s = s.replace(anchor, anchor + "\n" + insert, 1)

# replace readyz handler body to use helper
s = re.sub(
    r'@app\.get\("/readyz"\)\nasync def readyz\(\):\n\s*try:\n[\s\S]*?return JSONResponse\([\s\S]*?\)\n',
    '@app.get("/readyz")\nasync def readyz():\n    ok, payload = await _measure_readyz()\n    if ok:\n        return payload\n    return JSONResponse(payload, status_code=503)\n',
    s,
    count=1
)

p.write_text(s, encoding="utf-8")
print("OK: readyz now returns latency payload")
