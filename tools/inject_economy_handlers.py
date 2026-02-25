from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure economy cmd functions exist (quick sanity)
needed = ["async def ref_cmd", "async def my_cmd", "async def buy_cmd", "async def claim_cmd", "async def pending_cmd", "async def approve_cmd", "async def reject_cmd"]
missing = [x for x in needed if x not in s]
if missing:
    raise SystemExit("ERROR: missing functions in app_factory.py: " + ", ".join(missing))

# Find the end of build_application() and inject handlers before return app
m = re.search(r"(?m)^\s*return\s+app\s*$", s)
if not m:
    raise SystemExit("ERROR: could not find 'return app' in build_application()")

inject = """
    # === Economy commands (Commit A) ===
    app.add_handler(CommandHandler("ref", with_latency("ref", ref_cmd)))
    app.add_handler(CommandHandler("my", with_latency("my", my_cmd)))
    app.add_handler(CommandHandler("buy", with_latency("buy", buy_cmd)))
    app.add_handler(CommandHandler("claim", with_latency("claim", claim_cmd)))
    app.add_handler(CommandHandler("pending", with_latency("pending", pending_cmd)))
    app.add_handler(CommandHandler("approve", with_latency("approve", approve_cmd)))
    app.add_handler(CommandHandler("reject", with_latency("reject", reject_cmd)))
"""

# Only inject once
if "Economy commands (Commit A)" not in s:
    s = s[:m.start()] + inject + "\n" + s[m.start():]

p.write_text(s, encoding="utf-8")
print("OK: injected economy handlers before return app")
