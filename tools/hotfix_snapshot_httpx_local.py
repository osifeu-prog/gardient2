from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Force snapshot_cmd to import httpx locally
pattern = r'async def snapshot_cmd\([\s\S]*?\n(?=async def admin_cmd)'
replacement = r'''async def snapshot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("Access denied.")
        return

    import httpx  # local import to avoid NameError

    base = "https://gardient2-production.up.railway.app"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            version = (await client.get(f"{base}/version")).text.strip()
            healthz = (await client.get(f"{base}/healthz")).text.strip()
            readyz  = (await client.get(f"{base}/readyz")).text.strip()
            snap    = (await client.get(f"{base}/snapshot")).text.strip()

        msg = "\\n".join([
            "SNAPSHOT",
            f"base: {base}",
            "",
            f"/version: {version}",
            f"/healthz: {healthz}",
            f"/readyz:  {readyz}",
            f"/snapshot: {snap}",
        ])
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"snapshot error: {type(e).__name__}: {e}")

'''
s, n = re.subn(pattern, replacement, s, count=1)
if n != 1:
    raise SystemExit("ERROR: snapshot_cmd block not found")

p.write_text(s, encoding="utf-8")
print("OK: snapshot_cmd fixed with local httpx import")
