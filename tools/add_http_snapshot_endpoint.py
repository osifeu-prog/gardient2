from pathlib import Path

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

if '@app.get("/snapshot")' not in s:
    # Insert before /metrics endpoint
    marker = '@app.get("/metrics")'
    snippet = '''
@app.get("/snapshot")
async def snapshot():
    # lightweight JSON snapshot for ops
    return {
        "ok": True,
        "healthz": await healthz(),
        "version": await version(),
        "readyz": await readyz(),
    }

'''
    s = s.replace(marker, snippet + marker, 1)

p.write_text(s, encoding="utf-8")
print("OK: added GET /snapshot")
