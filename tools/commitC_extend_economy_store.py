from pathlib import Path
import re

p = Path("bot/economy_store.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Append accounts + pricing helpers if missing
if "async def add_account(" not in s:
    s += """

async def add_account(user_id: int, acc_type: str, label: str, details: dict) -> int:
    acc_id = _now_ms()
    import json
    async with get_db_session() as s:
        await s.execute(
            text(\"\"\"
                INSERT INTO accounts(id,user_id,type,label,details_json)
                VALUES (:id,:uid,:t,:label,:dj)
            \"\"\"),
            {
                "id": int(acc_id),
                "uid": int(user_id),
                "t": acc_type,
                "label": label,
                "dj": json.dumps(details, ensure_ascii=False),
            },
        )
        await s.commit()
    return int(acc_id)

async def list_accounts(user_id: int, limit: int = 10):
    async with get_db_session() as s:
        r = await s.execute(
            text(\"\"\"
                SELECT id,type,label,details_json,created_at
                FROM accounts
                WHERE user_id=:u
                ORDER BY created_at DESC
                LIMIT :lim
            \"\"\"),
            {"u": int(user_id), "lim": int(limit)},
        )
        out = []
        for row in r.fetchall():
            out.append({"id": int(row[0]), "type": row[1], "label": row[2], "details_json": row[3], "created_at": str(row[4])})
        return out

async def set_plan_price(code: str, amount: int, currency: str = "SELHA") -> None:
    async with get_db_session() as s:
        await s.execute(
            text(\"\"\"
                INSERT INTO plans(code,name,price_amount,price_currency,is_active)
                VALUES (:c,:n,:amt,:cur,true)
                ON CONFLICT (code)
                DO UPDATE SET price_amount=EXCLUDED.price_amount, price_currency=EXCLUDED.price_currency, is_active=true
            \"\"\"),
            {"c": code, "n": code, "amt": int(amount), "cur": currency},
        )
        await s.commit()

async def list_plans():
    async with get_db_session() as s:
        r = await s.execute(text("SELECT code,name,price_amount,price_currency,is_active FROM plans ORDER BY code"))
        out = []
        for row in r.fetchall():
            out.append({"code": row[0], "name": row[1], "price_amount": int(row[2]), "price_currency": row[3], "is_active": bool(row[4])})
        return out
"""

p.write_text(s, encoding="utf-8")
print("OK: extended bot/economy_store.py (accounts + plans)")
