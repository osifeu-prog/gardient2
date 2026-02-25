from __future__ import annotations
from typing import Optional, List, Dict

from sqlalchemy import text
from bot.infrastructure import get_db_session


async def has_role(tg_user_id: int, role_name: str) -> bool:
    async with get_db_session() as s:
        r = await s.execute(
            text("""
                SELECT 1
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = :uid AND r.name = :role
                LIMIT 1
            """),
            {"uid": int(tg_user_id), "role": role_name},
        )
        return r.first() is not None


async def grant_role(tg_user_id: int, role_name: str, granted_by: Optional[int] = None) -> None:
    async with get_db_session() as s:
        rid = await s.execute(text("SELECT id FROM roles WHERE name=:n"), {"n": role_name})
        row = rid.first()
        if not row:
            raise ValueError(f"role not found: {role_name}")
        role_id = int(row[0])

        await s.execute(
            text("""
                INSERT INTO user_roles(user_id, role_id, granted_by)
                VALUES (:uid, :rid, :gb)
                ON CONFLICT DO NOTHING
            """),
            {"uid": int(tg_user_id), "rid": role_id, "gb": (int(granted_by) if granted_by is not None else None)},
        )
        await s.commit()


async def revoke_role(tg_user_id: int, role_name: str) -> None:
    async with get_db_session() as s:
        await s.execute(
            text("""
                DELETE FROM user_roles
                WHERE user_id=:uid AND role_id=(SELECT id FROM roles WHERE name=:n)
            """),
            {"uid": int(tg_user_id), "n": role_name},
        )
        await s.commit()


async def list_users_with_role(role_name: str) -> List[Dict]:
    async with get_db_session() as s:
        r = await s.execute(
            text("""
                SELECT ur.user_id, ur.granted_by, ur.granted_at
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE r.name = :role
                ORDER BY ur.granted_at DESC
            """),
            {"role": role_name},
        )
        out: List[Dict] = []
        for row in r.fetchall():
            out.append({
                "user_id": int(row[0]),
                "granted_by": (int(row[1]) if row[1] is not None else None),
                "granted_at": str(row[2]),
            })
        return out
