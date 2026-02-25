from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

if "BotCommand" not in s:
    s = s.replace("from telegram import Update", "from telegram import Update\nfrom telegram import BotCommand")

# Find post_init function block (simple anchor) and append commands call inside it (once)
m = re.search(r"(?m)^async def post_init\(app\):\n([\s\S]*?)(?=^\S)", s)
if not m:
    raise SystemExit("ERROR: post_init not found")

block = m.group(0)
if "await app.bot.set_my_commands" not in block:
    insert = """
    # Telegram official commands (autocomplete)
    try:
        await app.bot.set_my_commands([
            BotCommand("start","Start"),
            BotCommand("menu","Show menu"),
            BotCommand("status","Infra status"),
            BotCommand("health","Health report"),
            BotCommand("whoami","User info"),
            BotCommand("donate","Support / donate"),
            BotCommand("admins","List admins"),
            BotCommand("grant_admin","(owner) Grant admin"),
            BotCommand("revoke_admin","(owner) Revoke admin"),
            BotCommand("dm","DM a user (admin)"),
            BotCommand("broadcast_admins","(owner) Broadcast to admins"),
        ])
    except Exception:
        pass
"""
    # Put it at end of post_init block
    block2 = block + "\n" + insert + "\n"
    s = s.replace(block, block2, 1)

p.write_text(s, encoding="utf-8")
print("OK: ensured set_my_commands in post_init")
