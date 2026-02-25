from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# 1) Ensure import BotCommand
if "from telegram import BotCommand" not in s:
    s = s.replace("from telegram import Update", "from telegram import Update\nfrom telegram import BotCommand")

# 2) Patch start_cmd command list (add donate/admin cmds text)
s = s.replace(
    "Commands:\n"
    "/status    DB/Redis/Alembic status\n"
    "/menu      menu\n"
    "/whoami    who am I\n"
    "/health    system health\n",
    "Commands:\n"
    "/status    DB/Redis/Alembic status\n"
    "/menu      menu\n"
    "/whoami    who am I\n"
    "/health    system health\n"
    "/donate    support / donate\n"
    "/admins    list admins (access-controlled)\n"
)

# 3) Patch menu_cmd to include new cmds (simple replace of the line that defines lines list)
s = re.sub(
    r'(?m)^\s*lines\s*=\s*\[.*\]\s*$',
    '    lines = ["Commands:", "/start", "/status", "/menu", "/whoami", "/health", "/donate", "/admins", "/grant_admin", "/revoke_admin", "/dm", "/broadcast_admins"]',
    s,
    count=1
)

# 4) Ensure post_init sets my commands (insert once)
m = re.search(r"(?m)^async def post_init\(app\):\n([\s\S]*?)(?=^\S)", s)
if not m:
    raise SystemExit("ERROR: post_init block not found")

block = m.group(0)
if "set_my_commands" not in block:
    inject = """
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
    # put it after init_infrastructure call if present
    if "await init_infrastructure()" in block:
        block2 = block.replace("await init_infrastructure()", "await init_infrastructure()\n" + inject)
    else:
        block2 = block + "\n" + inject
    s = s.replace(block, block2, 1)

p.write_text(s, encoding="utf-8")
print("OK: patched start/menu/setMyCommands")
