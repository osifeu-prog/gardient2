from pathlib import Path

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# 1) Add BOT_CMDS counter once
if "bot_commands_total" not in s:
    marker = "LAT = Histogram("
    idx = s.find(marker)
    if idx == -1:
        raise SystemExit("ERROR: LAT Histogram not found in server.py")

    # Insert after the LAT block ends: find the first occurrence of "\n)\n\nptb_app"
    end = s.find("\n)\n\nptb_app", idx)
    if end == -1:
        raise SystemExit("ERROR: could not locate end of LAT block")

    insert = '\n\nBOT_CMDS = Counter(\n    "bot_commands_total",\n    "Bot commands total",\n    ["cmd"],\n    registry=REGISTRY,\n)\n'
    s = s[:end+3] + insert + s[end+3:]

# 2) Increment counter in tg_webhook before Update.de_json
needle = "update = Update.de_json(payload, ptb_app.bot)"
if needle in s and "BOT_CMDS.labels" not in s:
    inc = '''# Count /commands from Telegram updates (best-effort)
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
    s = s.replace(needle, inc + needle, 1)

p.write_text(s, encoding="utf-8")
print("OK: bot_commands_total added to server.py")
