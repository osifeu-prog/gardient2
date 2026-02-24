from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure httpx import exists
if "import httpx" not in s:
    s = s.replace("import time\n", "import time\nimport httpx\n", 1)

# Insert snapshot_cmd before admin_cmd (if missing)
if "async def snapshot_cmd" not in s:
    insert = '''
async def snapshot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("Access denied.")
        return

    base = "https://gardient2-production.up.railway.app"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            version = (await client.get(f"{base}/version")).text.strip()
            healthz = (await client.get(f"{base}/healthz")).text.strip()
            readyz  = (await client.get(f"{base}/readyz")).text.strip()

        msg = "\\n".join([
            "SNAPSHOT",
            f"base: {base}",
            "",
            f"/version: {version}",
            f"/healthz: {healthz}",
            f"/readyz:  {readyz}",
        ])
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"snapshot error: {type(e).__name__}: {e}")
'''
    s = s.replace("async def admin_cmd", insert + "\n\nasync def admin_cmd", 1)

# Register handler in build_application if missing
if 'CommandHandler("snapshot"' not in s:
    s = s.replace(
        'app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))',
        'app.add_handler(CommandHandler("snapshot", with_latency("snapshot", snapshot_cmd)))\n    app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))',
        1
    )

p.write_text(s, encoding="utf-8")
print("OK: re-added /snapshot safely")
