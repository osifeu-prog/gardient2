from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure imports
if "from bot.economy_store" not in s:
    s = s.replace(
        "from bot.config import DONATE_URL",
        "from bot.config import DONATE_URL\nfrom bot.economy_store import (\n    create_payment_request, list_pending_requests, get_request, set_request_status,\n    add_points, get_points_balance, list_user_requests,\n    upsert_referral, get_referrer,\n)\n"
    )

# Helper: parse int safely
if "def _parse_amount" not in s:
    s = s.replace("def with_latency", "def _parse_amount(x: str) -> int:\n    return int(str(x).strip())\n\n\ndef with_latency")

# Add /ref command
if "async def ref_cmd" not in s:
    insert_point = re.search(r"(?m)^async def donate_cmd\\(", s)
    if not insert_point:
        raise SystemExit("ERROR: cannot find donate_cmd anchor")
    idx = insert_point.start()
    block = """
async def ref_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u:
        await update.message.reply_text("No user.")
        return
    bot_user = await context.bot.get_me()
    link = f"https://t.me/{bot_user.username}?start=ref_{u.id}"
    await update.message.reply_text("REFERRAL LINK\\n" + link)

"""
    s = s[:idx] + block + s[idx:]

# Add /my command
if "async def my_cmd" not in s:
    insert_point = re.search(r"(?m)^async def ref_cmd\\(", s)
    if not insert_point:
        raise SystemExit("ERROR: cannot find ref_cmd anchor")
    idx = insert_point.end()
    block = """
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

"""
    s = s[:idx] + block + s[idx:]

# Add /buy and /claim
if "async def buy_cmd" not in s:
    anchor = re.search(r"(?m)^async def my_cmd\\(", s)
    idx = anchor.end()
    block = """
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

"""
    s = s[:idx] + block + s[idx:]

# Admin inbox: /pending /approve /reject
if "async def pending_cmd" not in s:
    anchor = re.search(r"(?m)^async def claim_cmd\\(", s)
    idx = anchor.end()
    block = """
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

    # approve
    await set_request_status(rid, "approved", decided_by=int(update.effective_user.id))

    # award points 1:1
    await add_points(int(req["user_id"]), int(req["amount"]), reason=req["kind"], ref=str(rid))

    # referral bonus (5%)
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

"""
    s = s[:idx] + block + s[idx:]

# Referral capture: on /start with ref_...
# Very light: if /start has args and startswith ref_, insert into referrals
if "ref_" in s and "upsert_referral" in s and "start ref hook" not in s:
    # patch inside start_cmd at beginning
    pat = r"(?m)^async def start_cmd\\(update: Update, context: ContextTypes\\.DEFAULT_TYPE\\):"
    m = re.search(pat, s)
    if not m:
        raise SystemExit("ERROR: start_cmd not found")
    start_pos = m.end()
    inject = """
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
    s = s[:start_pos] + "\n" + inject + s[start_pos:]

# Register handlers
def ensure_handler(cmd, fn):
    nonlocal s
    if f'CommandHandler("{cmd}"' in s:
        return
    s = s.replace(
        "app.add_handler(CommandHandler(\"admin\", with_latency(\"admin\", admin_cmd)))",
        f'app.add_handler(CommandHandler("admin", with_latency("admin", admin_cmd)))\n'
        f'    app.add_handler(CommandHandler("{cmd}", with_latency("{cmd}", {fn})))'
    )

# Insert registration near existing handlers (after donate)
if 'CommandHandler("buy"' not in s:
    s = s.replace(
        'app.add_handler(CommandHandler("donate", with_latency("donate", donate_cmd)))',
        'app.add_handler(CommandHandler("donate", with_latency("donate", donate_cmd)))\n'
        '    app.add_handler(CommandHandler("ref", with_latency("ref", ref_cmd)))\n'
        '    app.add_handler(CommandHandler("my", with_latency("my", my_cmd)))\n'
        '    app.add_handler(CommandHandler("buy", with_latency("buy", buy_cmd)))\n'
        '    app.add_handler(CommandHandler("claim", with_latency("claim", claim_cmd)))\n'
        '    app.add_handler(CommandHandler("pending", with_latency("pending", pending_cmd)))\n'
        '    app.add_handler(CommandHandler("approve", with_latency("approve", approve_cmd)))\n'
        '    app.add_handler(CommandHandler("reject", with_latency("reject", reject_cmd)))'
    )

p.write_text(s, encoding="utf-8")
print("OK: patched app_factory with economy commands")
