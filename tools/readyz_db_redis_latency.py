from pathlib import Path
import re

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Replace readyz to return detailed latency
pattern = r'@app\.get\("/readyz"\)\nasync def readyz\(\):\n[\s\S]*?\n\n'
replacement = '''@app.get("/readyz")
async def readyz():
    t0 = time.perf_counter()
    payload = {"ok": True}

    try:
        from bot.infrastructure import check_postgres, check_redis
        tdb = time.perf_counter()
        await check_postgres()
        payload["db_ms"] = int((time.perf_counter() - tdb) * 1000)
        payload["db_ok"] = True
    except Exception as e:
        payload["db_ok"] = False
        payload["db_error"] = f"{type(e).__name__}: {e}"
        payload["ok"] = False

    try:
        tred = time.perf_counter()
        await check_redis()
        payload["redis_ms"] = int((time.perf_counter() - tred) * 1000)
        payload["redis_ok"] = True
    except Exception as e:
        payload["redis_ok"] = False
        payload["redis_error"] = f"{type(e).__name__}: {e}"
        payload["ok"] = False

    payload["elapsed_ms"] = int((time.perf_counter() - t0) * 1000)

    if payload["ok"]:
        return payload
    return JSONResponse(payload, status_code=503)

'''
s, n = re.subn(pattern, replacement, s, count=1)
if n != 1:
    raise SystemExit("ERROR: readyz endpoint not found")

p.write_text(s, encoding="utf-8")
print("OK: readyz now returns db_ms/redis_ms")
