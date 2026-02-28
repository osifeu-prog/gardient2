from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, time, secrets, json
from typing import Any
from eth_account.messages import encode_defunct
from eth_account import Account
import redis

router = APIRouter(prefix="/auth/wallet", tags=["auth-wallet"])

CHALLENGE_TTL_S = 300  # 5 minutes
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
rdb = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def k_nonce(nonce: str) -> str:
    return f"wallet_challenge:{nonce}"

class ChallengeIn(BaseModel):
    telegram_user_id: int | None = None
    purpose: str = "link_wallet"

class ChallengeOut(BaseModel):
    nonce: str
    message: str
    expires_in_s: int

class VerifyIn(BaseModel):
    nonce: str
    address: str
    signature: str
    telegram_user_id: int | None = None

@router.post("/challenge", response_model=ChallengeOut)
def challenge(body: ChallengeIn):
    nonce = secrets.token_urlsafe(24)
    now = int(time.time())
    exp = now + CHALLENGE_TTL_S
    app_name = os.getenv("APP_NAME", "Guardian")
    msg = (
        f"{app_name} wallet link\n"
        f"purpose={body.purpose}\n"
        f"nonce={nonce}\n"
        f"ts={now}\n"
        f"expires={exp}\n"
    )
    payload = {"exp": exp, "purpose": body.purpose, "telegram_user_id": body.telegram_user_id, "message": msg}
    rdb.setex(k_nonce(nonce), CHALLENGE_TTL_S, json.dumps(payload))
    return ChallengeOut(nonce=nonce, message=msg, expires_in_s=CHALLENGE_TTL_S)

@router.post("/verify")
def verify(body: VerifyIn):
    raw = rdb.get(k_nonce(body.nonce))
    if not raw:
        raise HTTPException(status_code=400, detail="unknown nonce")
    rec = json.loads(raw)
    if int(time.time()) > int(rec["exp"]):
        rdb.delete(k_nonce(body.nonce))
        raise HTTPException(status_code=400, detail="nonce expired")

    msg = encode_defunct(text=rec["message"])
    try:
        recovered = Account.recover_message(msg, signature=body.signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"bad signature: {e}")

    if recovered.lower() != body.address.lower():
        raise HTTPException(status_code=400, detail="signature does not match address")

    rdb.delete(k_nonce(body.nonce))
    return {"ok": True, "address": body.address, "telegram_user_id": body.telegram_user_id}
