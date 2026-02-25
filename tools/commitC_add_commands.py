from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# import additions
if "add_account" not in s:
    s = s.replace(
        "from bot.economy_store import (",
        "from bot.economy_store import (\n    add_account, list_accounts, set_plan_price, list_plans,"
    )

# --- Commands implementations (append before donate_cmd) ---
marker = re.search(r"(?m)^async def donate_cmd\(", s)
if not marker:
    raise SystemExit("ERROR: donate_cmd not found")

if "async def add_account_cmd" not in s:
    block = """
async def add_account_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u:
        await update.message.reply_text("No user.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /add_account <bank|crypto> <label> <details...>\\nExample: /add_account crypto MyTON address=UQ...\\nExample: /add_account bank MyBank bank=Hapoalim branch=123 account=456")
        return

    acc_type = context.args[0].lower()
    if acc_type not in ("bank","crypto"):
        await update.message.reply_text("First arg must be bank or crypto.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add_account <bank|crypto> <label> <details...>")
        return

    label = context.args[1]
    details = {}
    for token in context.args[2:]:
        if "=" in token:
            k,v = token.split("=",1)
            details[k.strip()] = v.strip()
        else:
            # free text goes into note
            details.setdefault("note", "")
            details["note"] = (details["note"] + " " + token).strip()

    acc_id = await add_account(int(u.id), acc_type, label, details)
    await update.message.reply_text(f"OK: account saved #{acc_id}")

async def prices_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plans = await list_plans()
    lines = ["PRICES:"]
    if not plans:
        lines.append("(none)")
    else:
        for p in plans:
            lines.append(f"- {p['code']}: {p['price_amount']} {p['price_currency']} ({'active' if p['is_active'] else 'inactive'})")
    await update.message.reply_text("\\n".join(lines))

async def set_price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("Access denied.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /set_price <plan_code> <amount>")
        return
    code = context.args[0]
    amt = _parse_amount(context.args[1])
    await set_plan_price(code, amt, "SELHA")
    await update.message.reply_text(f"OK: price set {code} = {amt} SELHA")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # manual trading wizard (request -> approve)
    u = update.effective_user
    if not u:
        await update.message.reply_text("No user.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /trade <buy|sell> <amount> [note]\\nExample: /trade buy 100\\nExample: /trade sell 50 reason=takeprofit")
        return
    side = context.args[0].lower()
    if side not in ("buy","sell"):
        await update.message.reply_text("First arg must be buy or sell.")
        return
    amt = _parse_amount(context.args[1])
    note = " ".join(context.args[2:]) if len(context.args) > 2 else None
    kind = "buy_token" if side == "buy" else "sell_token"
    req_id = await create_payment_request(int(u.id), kind, amt, "SELHA", note=note)
    await update.message.reply_text(f"OK: trade request created #{req_id} ({kind}) [pending]")
"""
    s = s[:marker.start()] + block + "\n\n" + s[marker.start():]

# Register handlers (inject near existing economy handlers anchor)
def ensure_handler(cmd, fn):
    global s
    if f'CommandHandler("{cmd}"' in s:
        return
    # inject near other handlers: before return app
    m = re.search(r"(?m)^\s*return\s+app\s*$", s)
    if not m:
        raise SystemExit("ERROR: return app not found")
    inject = f'    app.add_handler(CommandHandler("{cmd}", with_latency("{cmd}", {fn})))\n'
    s = s[:m.start()] + inject + s[m.start():]

ensure_handler("add_account", "add_account_cmd")
ensure_handler("prices", "prices_cmd")
ensure_handler("set_price", "set_price_cmd")
ensure_handler("trade", "trade_cmd")

p.write_text(s, encoding="utf-8")
print("OK: added commitC commands + handlers")
