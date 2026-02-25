from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure menu_registry import exists
if "from bot.menu_registry import COMMANDS, visible" not in s:
    raise SystemExit("ERROR: menu_registry import missing - Commit B not applied locally?")

# Ensure resolve_role exists
if "async def resolve_role(" not in s:
    raise SystemExit("ERROR: resolve_role() missing")

# Replace entire start_cmd block deterministically (from 'async def start_cmd' until next 'async def')
m = re.search(r"(?ms)^async def start_cmd\(.*?\n(?=async def |\Z)", s)
if not m:
    raise SystemExit("ERROR: start_cmd block not found")

new_block = """async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = await resolve_role(update)
    cmds = visible(COMMANDS, role, for_start=True, for_menu=False)

    lines = [
        f"```\\n{ASCII_BANNER.strip()}\\n```",
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

s = s[:m.start()] + new_block + "\n\n" + s[m.end():]
p.write_text(s, encoding="utf-8")
print("OK: start_cmd replaced with dynamic version")
