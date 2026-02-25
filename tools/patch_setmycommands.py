from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure we import BotCommand
if "BotCommand" not in s:
    s = s.replace("from telegram import Update", "from telegram import Update\nfrom telegram import BotCommand")

# Patch post_init to set commands
m = re.search(r"(?m)^async def post_init\(app\):\n([\s\S]*?)(?=^\S)", s)
if not m:
    raise SystemExit("ERROR: post_init not found")

block = m.group(0)
if "set_my_commands" not in block:
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
    # Insert near end of post_init (before app build return)
    block2 = block + insert + "\n"
    s = s.replace(block, block2, 1)

p.write_text(s, encoding="utf-8")
print("OK: added set_my_commands to post_init")
