from pathlib import Path
import re

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Replace snapshot endpoint body to return a flat dict
pattern = r'@app\.get\("/snapshot"\)\nasync def snapshot\(\):\n[\s\S]*?\n\n'
replacement = '''@app.get("/snapshot")
async def snapshot():
    import datetime
    v = await version()
    h = await healthz()
    r = await readyz()
    return {
        "ok": True,
        "ts_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "service": v.get("service"),
        "git_sha": v.get("git_sha"),
        "uptime_s": v.get("uptime_s"),
        "healthz": h,
        "readyz": r,
        "webhook": "/tg/webhook",
    }

'''
s, n = re.subn(pattern, replacement, s, count=1)
if n != 1:
    raise SystemExit("ERROR: snapshot endpoint not found")

p.write_text(s, encoding="utf-8")
print("OK: snapshot endpoint flattened")
