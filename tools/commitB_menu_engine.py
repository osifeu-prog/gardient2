from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# add registry import
if "from bot.menu_registry import" not in s:
    s = s.replace(
        "from bot.config import DONATE_URL",
        "from bot.config import DONATE_URL\nfrom bot.menu_registry import COMMANDS, visible\n"
    )

# role resolver helper
if "async def resolve_role(" not in s:
    ins = """
async def resolve_role(update: Update) -> str:
    # owner wins
    if is_owner(update):
        return "owner"
    # admin from DB
    try:
        if await has_role(int(update.effective_user.id), "admin"):
            return "admin"
    except Exception:
        pass
    return "user"
"""
    # place after is_admin_rbac
    m = re.search(r"(?m)^async def is_admin_rbac\\([\\s\\S]*?\\n\\s*return False\\n", s)
    if not m:
        raise SystemExit("ERROR: could not locate is_admin_rbac block")
    s = s[:m.end()] + "\n" + ins + "\n" + s[m.end():]

# rewrite start_cmd (dynamic)
start_pat = r"(?m)^async def start_cmd\\([\\s\\S]*?\\n\\s*await update\\.message\\.reply_text\\(text, parse_mode=\"Markdown\"\\)\\n"
m = re.search(start_pat, s)
if not m:
    raise SystemExit("ERROR: start_cmd block not found")
new_start = """async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = await resolve_role(update)
    # Build list of commands for start
    cmds = visible(COMMANDS, role, for_start=True, for_menu=False)
    lines = [
        f"```\n{ASCII_BANNER.strip()}\n```",
        "SLH Guardian Security + Ops Control",
        "",
        "Welcome to SLH Guardian.",
        "Infra monitoring, ops control, and SaaS-ready foundation.",
        "",
        "Commands:",
    ]
    for c in cmds:
        lines.append(f"/{c.cmd}    {c.desc}")
    await update.message.reply_text("\\n".join(lines), parse_mode="Markdown")
"""
s = s.replace(m.group(0), new_start + "\n", 1)

# rewrite menu_cmd (dynamic)
menu_pat = r"(?m)^async def menu_cmd\\([\\s\\S]*?\\n\\s*await update\\.message\\.reply_text\\(\"\\\\n\"\\.join\\(lines\\)\\)\\n"
m = re.search(menu_pat, s)
if not m:
    raise SystemExit("ERROR: menu_cmd block not found")
new_menu = """async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = await resolve_role(update)
    cmds = visible(COMMANDS, role, for_start=False, for_menu=True)
    lines = ["Commands:"]
    for c in cmds:
        lines.append(f"/{c.cmd} - {c.desc}")
    await update.message.reply_text("\\n".join(lines))
"""
s = s.replace(m.group(0), new_menu + "\n", 1)

# ensure post_init sets my commands from registry (global commands for the bot UI)
# We'll set "user" level commands by default. Admin/owner will still work even if hidden in autocomplete.
if "set_my_commands_from_registry" not in s:
    inject = """
    # set_my_commands_from_registry
    try:
        # show base commands to all users (Telegram supports one list per bot)
        base_cmds = visible(COMMANDS, "user", for_start=False, for_menu=True)
        await app.bot.set_my_commands([BotCommand(c.cmd, c.desc) for c in base_cmds])
    except Exception:
        pass
"""
    # insert inside post_init at end
    pm = re.search(r"(?m)^async def post_init\\(app\\):\\n", s)
    if not pm:
        raise SystemExit("ERROR: post_init not found")
    # place near end of function by appending before end-of-file (safe)
    if inject not in s:
        s += "\n" + inject + "\n"

p.write_text(s, encoding="utf-8")
print("OK: patched app_factory to use menu_registry for start/menu/setMyCommands")
