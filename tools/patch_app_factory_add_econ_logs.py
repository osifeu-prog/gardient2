from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure import
if "from bot.telemetry import log_event" not in s:
    s = s.replace(
        "from bot.telemetry import log_json, exc_to_str, update_brief",
        "from bot.telemetry import log_json, exc_to_str, update_brief, log_event"
    )

# Add log hooks inside buy/claim/approve/reject/ref and my
def add_after(pattern, insert, once=True):
    global s
    m = re.search(pattern, s, flags=re.M)
    if not m:
        raise SystemExit("ERROR: pattern not found for insert")
    pos = m.end()
    s = s[:pos] + insert + s[pos:]

# buy_cmd: after req_id created
if "economy_request_created" not in s:
    s = s.replace(
        'await update.message.reply_text(f"OK: buy request created #{req_id} (pending)")',
        'log_event(logging.INFO, "economy_request_created", kind="buy_token", request_id=req_id, amount=amt, user_id=int(u.id), username=(u.username or None))\n    await update.message.reply_text(f"OK: buy request created #{req_id} (pending)")'
    )

# claim_cmd: after req_id created
s = s.replace(
    'await update.message.reply_text(f"OK: donation claim created #{req_id} (pending)")',
    'log_event(logging.INFO, "economy_request_created", kind="donate", request_id=req_id, amount=amt, user_id=int(u.id), username=(u.username or None), tx_ref=tx)\n    await update.message.reply_text(f"OK: donation claim created #{req_id} (pending)")'
)

# ref_cmd: log link creation
if "referral_link_issued" not in s:
    s = s.replace(
        'await update.message.reply_text("REFERRAL LINK\\n" + link)',
        'log_event(logging.INFO, "referral_link_issued", user_id=int(u.id), username=(u.username or None))\n    await update.message.reply_text("REFERRAL LINK\\n" + link)'
    )

# start ref hook: log linking (only on success)
if "referral_linked" not in s:
    s = s.replace(
        "await upsert_referral(ref_id, int(u.id))",
        "ok_link = await upsert_referral(ref_id, int(u.id))\n                if ok_link:\n                    log_event(logging.INFO, \"referral_linked\", referrer_id=ref_id, referred_id=int(u.id))"
    )

# approve_cmd: log decision + points + optional bonus
if "economy_request_decided" not in s:
    s = s.replace(
        'await update.message.reply_text(f"OK: approved #{rid} and awarded {req[\'amount\']} points")',
        'log_event(logging.INFO, "economy_request_decided", action="approve", request_id=rid, user_id=int(req["user_id"]), decided_by=int(update.effective_user.id), amount=int(req["amount"]), kind=req["kind"])\n    log_event(logging.INFO, "points_awarded", user_id=int(req["user_id"]), delta=int(req["amount"]), reason=req["kind"], ref=str(rid))\n    await update.message.reply_text(f"OK: approved #{rid} and awarded {req[\'amount\']} points")'
    )

# reject_cmd: log decision
s = s.replace(
    'await update.message.reply_text(f"OK: rejected #{rid}")',
    'log_event(logging.INFO, "economy_request_decided", action="reject", request_id=rid, decided_by=int(update.effective_user.id))\n    await update.message.reply_text(f"OK: rejected #{rid}")'
)

p.write_text(s, encoding="utf-8")
print("OK: patched app_factory with economy/referral logs")
