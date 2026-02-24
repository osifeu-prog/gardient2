from pathlib import Path
import re

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Add bot command metrics once (uses the same REGISTRY)
if 'bot_commands_total' not in s:
    add = '''
BOT_CMDS = Counter(
    "bot_commands_total",
    "Bot commands total",
    ["cmd"],
    registry=REGISTRY,
)
'''
    # Insert after REQS/LAT definitions (after LAT = Histogram block)
    s = s.replace("LAT = Histogram(", "LAT = Histogram(", 1)
    # put right after the LAT block end "registry=REGISTRY,\n)\n"
    s = s.replace("registry=REGISTRY,\n)\n\nptb_app = build_application()", "registry=REGISTRY,\n)\n\n" + add + "\nptb_app = build_application()", 1)

# In webhook handler, increment counter when a command is seen
# We'll parse the update JSON for message text that starts with "/"
if "BOT_CMDS.labels" not in s:
    hook = '''
    # lightweight command counter
    try:
        msg = payload.get("message") or payload.get("edited_message") or {}
        text = (msg.get("text") or "").strip()
        if text.startswith("/"):
            cmd = text.split()[0].split("@")[0].lstrip("/")
            if cmd:
                BOT_CMDS.labels(cmd=cmd).inc()
    except Exception:
        pass
'''
    s = s.replace("update = Update.de_json(payload, ptb_app.bot)", hook + "\n    update = Update.de_json(payload, ptb_app.bot)", 1)

p.write_text(s, encoding="utf-8")
print("OK: added bot command metrics")
