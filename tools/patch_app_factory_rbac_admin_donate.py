from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# 1) add imports (rbac + donate)
if "from bot.rbac_store" not in s:
    s = s.replace(
        "from bot.telemetry import log_json, exc_to_str, update_brief",
        "from bot.telemetry import log_json, exc_to_str, update_brief\nfrom bot.rbac_store import has_role, grant_role, revoke_role, list_users_with_role\nfrom bot.config import DONATE_URL"
    )

# 2) add helpers: is_owner / is_admin_rbac
if "def is_owner(" not in s:
    insert_after = "def is_admin(update: Update) -> bool:"
    m = re.search(r"(?m)^def is_admin\(update: Update\) -> bool:\n\s+return[^\n]*\n", s)
    if not m:
        raise SystemExit("ERROR: could not locate is_admin() function block")
    block = m.group(0)
    new = block + """
def is_owner(update: Update) -> bool:
    # owner is ADMIN_CHAT_ID (chat id)
    return bool(ADMIN_CHAT_ID) and str(update.effective_chat.id) == str(ADMIN_CHAT_ID)

async def is_admin_rbac(update: Update) -> bool:
    # owner always allowed; else admin role in DB
    if is_owner(update):
        return True
    try:
        return await has_role(int(update.effective_user.id), "admin")
    except Exception:
        # if DB not ready, fall back to legacy owner-only
        return False
"""
    s = s.replace(block, new)

# 3) add donate command
if "async def donate_cmd" not in s:
    # insert near other cmd funcs; we put it after health_cmd for clarity
    m = re.search(r"(?m)^async def health_cmd\([^\)]*\):[\s\S]*?\n\n", s)
    if not m:
        raise SystemExit("ERROR: could not locate health_cmd block")
    health_block = m.group(0)
    donate_block = health_block + """
async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DONATE_URL:
        await update.message.reply_text("Donations are not configured yet.")
        return
    await update.message.reply_text(f"DONATE / SUPPORT\\n{DONATE_URL}")
\n"""
    s = s.replace(health_block, donate_block, 1)

# 4) add admin RBAC commands (grant_admin/revoke_admin/admins/dm/broadcast_admins)
if "async def grant_admin_cmd" not in s:
    m = re.search(r"(?m)^async def admin_cmd\([^\)]*\):[\s\S]*?\n\n", s)
    if not m:
        raise SystemExit("ERROR: could not locate admin_cmd block")
    admin_block = m.group(0)

    extra = admin_block + """
async def grant_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /grant_admin <user_id>")
        return
    uid = int(context.args[0])
    await grant_role(uid, "admin", granted_by=int(update.effective_user.id))
    await update.message.reply_text(f"OK: granted admin to {uid}")

async def revoke_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /revoke_admin <user_id>")
        return
    uid = int(context.args[0])
    await revoke_role(uid, "admin")
    await update.message.reply_text(f"OK: revoked admin from {uid}")

async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_rbac(update):
        await update.message.reply_text("Access denied.")
        return
    admins = await list_users_with_role("admin")
    lines = ["ADMINS:"]
    if not admins:
        lines.append("(none)")
    else:
        for a in admins:
            lines.append(f"- {a['user_id']} (by {a['granted_by']} at {a['granted_at']})")
    await update.message.reply_text("\\n".join(lines))

async def dm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_rbac(update):
        await update.message.reply_text("Access denied.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /dm <user_id> <msg>")
        return
    uid = int(context.args[0])
    msg = " ".join(context.args[1:])
    await context.bot.send_message(chat_id=uid, text=msg)
    await update.message.reply_text("OK: sent.")

async def broadcast_admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast_admins <msg>")
        return
    msg = " ".join(context.args)
    admins = await list_users_with_role("admin")
    sent = 0
    for a in admins:
        try:
            await context.bot.send_message(chat_id=int(a["user_id"]), text=msg)
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"OK: broadcasted to {sent} admins.")
\n"""
    s = s.replace(admin_block, extra, 1)

# 5) seed owner role on post_init
m = re.search(r"(?m)^async def post_init\(app\):\n[\s\S]*?$", s)
if not m:
    raise SystemExit("ERROR: could not locate post_init()")

# insert seed right after init_infrastructure call
if "seed_owner_rbac" not in s:
    s = s.replace(
        "      await init_infrastructure()",
        "      await init_infrastructure()\n      # seed owner role into RBAC\n      try:\n          if ADMIN_CHAT_ID:\n              await grant_role(int(ADMIN_CHAT_ID), 'owner', granted_by=int(ADMIN_CHAT_ID))\n      except Exception:\n          pass"
    )

# 6) register handlers near existing add_handler list
# add after /health
if 'CommandHandler("donate"' not in s:
    s = s.replace(
        'app.add_handler(CommandHandler("health", with_latency("health", health_cmd)))',
        'app.add_handler(CommandHandler("health", with_latency("health", health_cmd)))\n    app.add_handler(CommandHandler("donate", with_latency("donate", donate_cmd)))'
    )

# add admin handlers near /admin
for cmd in ["grant_admin","revoke_admin","admins","dm","broadcast_admins"]:
    if f'CommandHandler("{cmd}"' not in s:
        # anchor after admin handler
        s = s.replace(
            'app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))',
            'app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))\n'
            '    app.add_handler(CommandHandler("grant_admin", with_latency("grant_admin", grant_admin_cmd)))\n'
            '    app.add_handler(CommandHandler("revoke_admin", with_latency("revoke_admin", revoke_admin_cmd)))\n'
            '    app.add_handler(CommandHandler("admins", with_latency("admins", admins_cmd)))\n'
            '    app.add_handler(CommandHandler("dm", with_latency("dm", dm_cmd)))\n'
            '    app.add_handler(CommandHandler("broadcast_admins", with_latency("broadcast_admins", broadcast_admins_cmd)))'
        )
        break

p.write_text(s, encoding="utf-8")
print("OK: patched bot/app_factory.py (RBAC seed + admin cmds + donate)")
