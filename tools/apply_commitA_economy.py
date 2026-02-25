from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure economy imports
if "from bot.economy_store import" not in s:
    s = s.replace(
        "from bot.config import DONATE_URL",
        "from bot.config import DONATE_URL\nfrom bot.economy_store import (\n    create_payment_request, list_pending_requests, get_request, set_request_status,\n    add_points, get_points_balance, list_user_requests,\n    upsert_referral, get_referrer,\n)\n"
    )

# Ensure parse helper
if "def _parse_amount" not in s:
    s = s.replace("def with_latency", "def _parse_amount(x: str) -> int:\n    return int(str(x).strip())\n\n\ndef with_latency")

# Add command functions if missing (append near donate_cmd)
def ensure_block(marker_pat: str, block: str):
    global s
    if block.strip() in s:
        return
    m = re.search(marker_pat, s, flags=re.M)
    if not m:
        raise SystemExit("ERROR: marker not found for insertion")
    s = s[:m.start()] + block + "\n\n" + s[m.start():]

if "async def ref_cmd" not in s:
    ensure_block(r"^async def donate_cmd\(", """
async def ref_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u:
        await update.message.reply_text("No user.")
        return
    bot_user = await context.bot.get_me()
    link = f"https://t.me/{bot_user.username}?start=ref_{u.id}"
    await update.message.reply_text("REFERRAL LINK\\n" + link)

async def my_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u:
        await update.message.reply_text("No user.")
        return
    bal = await get_points_balance(int(u.id))
    reqs = await list_user_requests(int(u.id), limit=5)
    lines = [
        "MY",
        f"user_id: {u.id}",
        f"points: {bal}",
        "",
        "Recent requests:",
    ]
    if not reqs:
        lines.append("(none)")
    else:
        for r in reqs:
            lines.append(f"- #{r['id']} {r['kind']} {r['amount']} {r['currency']} [{r['status']}]")
    await update.message.reply_text("\\n".join(lines))

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u:
        await update.message.reply_text("No user.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /buy <amount> [note]")
        return
    amt = _parse_amount(context.args[0])
    note = " ".join(context.args[1:]) if len(context.args) > 1 else None
    req_id = await create_payment_request(int(u.id), "buy_token", amt, "SELHA", note=note)
    await update.message.reply_text(f"OK: buy request created #{req_id} (pending)")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u:
        await update.message.reply_text("No user.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /claim <amount> <tx_ref> [note]")
        return
    amt = _parse_amount(context.args[0])
    tx = context.args[1]
    note = " ".join(context.args[2:]) if len(context.args) > 2 else None
    req_id = await create_payment_request(int(u.id), "donate", amt, "SELHA", tx_ref=tx, note=note)
    await update.message.reply_text(f"OK: donation claim created #{req_id} (pending)")

async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_rbac(update):
        await update.message.reply_text("Access denied.")
        return
    items = await list_pending_requests(limit=10)
    lines = ["PENDING REQUESTS:"]
    if not items:
        lines.append("(none)")
    else:
        for it in items:
            lines.append(f"- #{it['id']} user={it['user_id']} {it['kind']} {it['amount']} {it['currency']} tx={it['tx_ref'] or '-'}")
    await update.message.reply_text("\\n".join(lines))

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_rbac(update):
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /approve <request_id>")
        return
    rid = int(context.args[0])
    req = await get_request(rid)
    if not req or req["status"] != "pending":
        await update.message.reply_text("Not found or not pending.")
        return

    await set_request_status(rid, "approved", decided_by=int(update.effective_user.id))
    await add_points(int(req["user_id"]), int(req["amount"]), reason=req["kind"], ref=str(rid))

    referrer = await get_referrer(int(req["user_id"]))
    if referrer:
        bonus = max(1, int(int(req["amount"]) * 0.05))
        await add_points(int(referrer), bonus, reason="ref_bonus", ref=str(rid))

    await update.message.reply_text(f"OK: approved #{rid} and awarded {req['amount']} points")

async def reject_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_rbac(update):
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /reject <request_id>")
        return
    rid = int(context.args[0])
    req = await get_request(rid)
    if not req or req["status"] != "pending":
        await update.message.reply_text("Not found or not pending.")
        return
    await set_request_status(rid, "rejected", decided_by=int(update.effective_user.id))
    await update.message.reply_text(f"OK: rejected #{rid}")
""")

# Add start ref hook (idempotent)
if "start ref hook" not in s:
    m = re.search(r"(?m)^async def start_cmd\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):", s)
    if not m:
        raise SystemExit("ERROR: start_cmd not found")
    pos = m.end()
    hook = """
    # start ref hook
    try:
        if context.args and len(context.args) >= 1 and str(context.args[0]).startswith("ref_"):
            ref_id = int(str(context.args[0]).split("_", 1)[1])
            u = update.effective_user
            if u:
                await upsert_referral(ref_id, int(u.id))
    except Exception:
        pass
"""
    s = s[:pos] + "\n" + hook + s[pos:]

# Register handlers inside build_application() by injecting before 'return app'
m = re.search(r"(?m)^\s*return\s+app\s*$", s)
if not m:
    raise SystemExit("ERROR: return app not found")
if "Economy commands (Commit A)" not in s:
    inject = """
    # === Economy commands (Commit A) ===
    app.add_handler(CommandHandler("ref", with_latency("ref", ref_cmd)))
    app.add_handler(CommandHandler("my", with_latency("my", my_cmd)))
    app.add_handler(CommandHandler("buy", with_latency("buy", buy_cmd)))
    app.add_handler(CommandHandler("claim", with_latency("claim", claim_cmd)))
    app.add_handler(CommandHandler("pending", with_latency("pending", pending_cmd)))
    app.add_handler(CommandHandler("approve", with_latency("approve", approve_cmd)))
    app.add_handler(CommandHandler("reject", with_latency("reject", reject_cmd)))
"""
    s = s[:m.start()] + inject + "\n" + s[m.start():]

# Patch /menu to show new commands (temporary until Commit B)
s = s.replace(
    'lines = ["Commands:", "/start", "/status", "/menu", "/whoami", "/health", "/donate", "/admins", "/grant_admin", "/revoke_admin", "/dm", "/broadcast_admins"]',
    'lines = ["Commands:", "/start", "/status", "/menu", "/whoami", "/health", "/donate", "/admins", "/ref", "/my", "/buy", "/claim", "/grant_admin", "/revoke_admin", "/dm", "/broadcast_admins"]'
)

p.write_text(s, encoding="utf-8")
print("OK: economy commands + handlers added to app_factory")
