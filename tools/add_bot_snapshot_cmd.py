from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# 1) Add import httpx if missing (it is already used elsewhere in this file usually)
if "import httpx" not in s:
    # place near other imports
    s = s.replace("import time\n", "import time\nimport httpx\n", 1)

# 2) Add snapshot command function if missing
if "async def snapshot_cmd" not in s:
    insert = '''
async def snapshot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("? Access denied.")
        return

    base = "https://gardient2-production.up.railway.app"
    async with httpx.AsyncClient(timeout=10.0) as client:
        healthz = (await client.get(f"{base}/healthz")).text.strip()
        version = (await client.get(f"{base}/version")).text.strip()
        readyz  = (await client.get(f"{base}/readyz")).text.strip()

    msg = (
        "?? SNAPSHOT\\n"
        f"base: {base}\\n\\n"
        f"/version: {version}\\n"
        f"/healthz: {healthz}\\n"
        f"/readyz: {readyz}\\n"
    )
    await update.message.reply_text(msg)
'''
    # insert before admin_cmd definition
    s = s.replace("async def admin_cmd", insert + "\nasync def admin_cmd", 1)

# 3) Register handler if missing
if 'CommandHandler("snapshot"' not in s:
    s = s.replace(
        'app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))',
        'app.add_handler(CommandHandler("snapshot", with_latency("snapshot", snapshot_cmd)))\n    app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))',
        1
    )

p.write_text(s, encoding="utf-8")
print("OK: added /snapshot (admin-only) to bot")
