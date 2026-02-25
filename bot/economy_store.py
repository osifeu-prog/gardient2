from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from bot.infrastructure import get_db_session


def _now_ms() -> int:
    return int(time.time() * 1000)


async def create_payment_request(
    user_id: int,
    kind: str,
    amount: int,
    currency: str = "SELHA",
    tx_ref: Optional[str] = None,
    note: Optional[str] = None,
) -> int:
    req_id = _now_ms()
    async with get_db_session() as s:
        await s.execute(
            text("""
                INSERT INTO payment_requests(id,user_id,kind,amount,currency,tx_ref,note,status)
                VALUES (:id,:uid,:kind,:amt,:cur,:tx,:note,'pending')
            """),
            {"id": req_id, "uid": int(user_id), "kind": kind, "amt": int(amount), "cur": currency, "tx": tx_ref, "note": note},
        )
        await s.commit()
    return req_id


async def list_pending_requests(limit: int = 10) -> List[Dict[str, Any]]:
    async with get_db_session() as s:
        r = await s.execute(
            text("""
                SELECT id,user_id,kind,amount,currency,tx_ref,note,created_at
                FROM payment_requests
                WHERE status='pending'
                ORDER BY created_at ASC
                LIMIT :lim
            """),
            {"lim": int(limit)},
        )
        return [
            {"id": int(x[0]), "user_id": int(x[1]), "kind": x[2], "amount": int(x[3]), "currency": x[4], "tx_ref": x[5], "note": x[6], "created_at": str(x[7])}
            for x in r.fetchall()
        ]


async def get_request(req_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_session() as s:
        r = await s.execute(
            text("""
                SELECT id,user_id,kind,amount,currency,tx_ref,note,status,decided_by,decided_at,created_at
                FROM payment_requests
                WHERE id=:id
            """),
            {"id": int(req_id)},
        )
        row = r.first()
        if not row:
            return None
        return {
            "id": int(row[0]),
            "user_id": int(row[1]),
            "kind": row[2],
            "amount": int(row[3]),
            "currency": row[4],
            "tx_ref": row[5],
            "note": row[6],
            "status": row[7],
            "decided_by": (int(row[8]) if row[8] is not None else None),
            "decided_at": (str(row[9]) if row[9] is not None else None),
            "created_at": str(row[10]),
        }


async def set_request_status(req_id: int, status: str, decided_by: int) -> None:
    async with get_db_session() as s:
        await s.execute(
            text("""
                UPDATE payment_requests
                SET status=:st, decided_by=:db, decided_at=now()
                WHERE id=:id
            """),
            {"st": status, "db": int(decided_by), "id": int(req_id)},
        )
        await s.commit()


async def add_points(user_id: int, delta: int, reason: str, ref: Optional[str] = None) -> int:
    entry_id = _now_ms()
    async with get_db_session() as s:
        await s.execute(
            text("""
                INSERT INTO points_ledger(id,user_id,delta,reason,ref)
                VALUES (:id,:uid,:d,:r,:ref)
            """),
            {"id": entry_id, "uid": int(user_id), "d": int(delta), "r": reason, "ref": ref},
        )
        await s.commit()
    return entry_id


async def get_points_balance(user_id: int) -> int:
    async with get_db_session() as s:
        r = await s.execute(text("SELECT COALESCE(SUM(delta),0) FROM points_ledger WHERE user_id=:u"), {"u": int(user_id)})
        return int(r.scalar() or 0)


async def list_user_requests(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    async with get_db_session() as s:
        r = await s.execute(
            text("""
                SELECT id,kind,amount,currency,status,tx_ref,created_at,decided_at
                FROM payment_requests
                WHERE user_id=:u
                ORDER BY created_at DESC
                LIMIT :lim
            """),
            {"u": int(user_id), "lim": int(limit)},
        )
        out = []
        for row in r.fetchall():
            out.append({"id": int(row[0]), "kind": row[1], "amount": int(row[2]), "currency": row[3], "status": row[4], "tx_ref": row[5], "created_at": str(row[6]), "decided_at": (str(row[7]) if row[7] else None)})
        return out


async def upsert_referral(referrer_id: int, referred_id: int) -> bool:
    if int(referrer_id) == int(referred_id):
        return False
    async with get_db_session() as s:
        await s.execute(
            text("INSERT INTO referrals(referrer_id,referred_id) VALUES (:r,:u) ON CONFLICT DO NOTHING"),
            {"r": int(referrer_id), "u": int(referred_id)},
        )
        await s.commit()
    return True


async def get_referrer(referred_id: int) -> Optional[int]:
    async with get_db_session() as s:
        r = await s.execute(text("SELECT referrer_id FROM referrals WHERE referred_id=:u LIMIT 1"), {"u": int(referred_id)})
        row = r.first()
        return int(row[0]) if row else None
