from pathlib import Path
import re

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

pattern = r'@app\.get\("/readyz"\)\nasync def readyz\(\):\n[\s\S]*?\n\n'
replacement = '''@app.get("/readyz")
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

'''
s, n = re.subn(pattern, replacement, s, count=1)
if n != 1:
    raise SystemExit("ERROR: readyz endpoint not found in server.py")

p.write_text(s, encoding="utf-8")
print("OK: readyz reverted to runtime_report(full=False) (no recursion)")
