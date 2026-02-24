from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure import httpx exists
if "import httpx" not in s:
    s = s.replace("import time\n", "import time\nimport httpx\n", 1)

# Safe snapshot cmd (ASCII-only, no emoji, no broken quotes)
new_impl = r'''
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
            snap    = (await client.get(f"{base}/snapshot")).text.strip()

        msg = (
            "SNAPSHOT\n"
            f"base: {base}\n\n"
            f"/version: {version}\n"
            f"/healthz: {healthz}\n"
            f"/readyz:  {readyz}\n"
            f"/snapshot: {snap}\n"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"snapshot error: {type(e).__name__}: {e}")
'''

# Replace existing snapshot_cmd block if present, else insert before admin_cmd
if "async def snapshot_cmd" in s:
    s = re.sub(r'async def snapshot_cmd\([\s\S]*?\nasync def admin_cmd', new_impl + "\n\nasync def admin_cmd", s, count=1)
else:
    s = s.replace("async def admin_cmd", new_impl + "\n\nasync def admin_cmd", 1)

# Ensure handler is registered
if 'CommandHandler("snapshot"' not in s:
    s = s.replace(
        'app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))',
        'app.add_handler(CommandHandler("snapshot", with_latency("snapshot", snapshot_cmd)))\n    app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))',
        1
    )

p.write_text(s, encoding="utf-8")
print("OK: snapshot_cmd fixed (ASCII-safe)")
