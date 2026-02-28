from __future__ import annotations

import os, re, time, hashlib
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/tx", tags=["tx-send"])

RPC = (os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/") or "").strip()
REDIS_URL = (os.getenv("REDIS_URL", "") or "").strip()

# ---- config ----
RL_IP_PER_MIN = int((os.getenv("RL_SENDRAW_IP_PER_MIN", "10") or "10").strip())
RL_KEY_PER_MIN = int((os.getenv("RL_SENDRAW_KEY_PER_MIN", "60") or "60").strip())
RL_TTL_SEC = int((os.getenv("RL_SENDRAW_TTL_SEC", "70") or "70").strip())

TRANSFER_SELECTOR = "0xa9059cbb"
TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _token_allowlist() -> set[str]:
    raw = _env("GUARDIAN_TOKEN_ALLOWLIST", "")
    return set([x.strip().lower() for x in raw.split(",") if x.strip()])


def _require_internal_key(x_guardian_key: str | None):
    expected = _env("GUARDIAN_INTERNAL_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=500, detail="GUARDIAN_INTERNAL_API_KEY not set")
    if not x_guardian_key or x_guardian_key.strip() != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


def _is_hexhash(s: str) -> bool:
    return bool(re.fullmatch(r"0x[0-9a-fA-F]{64}", s or ""))


def _is_hex_tx(s: str) -> bool:
    return bool(re.fullmatch(r"0x[0-9a-fA-F]+", s or ""))


def _client_ip(request: Request) -> str:
    # Prefer forwarded headers if you later sit behind a proxy; keep it simple for now.
    xf = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if xf:
        return xf
    return (request.client.host if request.client else "unknown") or "unknown"


def _kid_from_key(x_guardian_key: str | None) -> str:
    if not x_guardian_key:
        return "none"
    h = hashlib.sha256(x_guardian_key.encode("utf-8")).hexdigest()
    return h[:12]


async def _rpc(method: str, params: Any, idv: int = 1):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": idv}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(RPC, json=payload)
        r.raise_for_status()
        j = r.json()
        if "error" in j:
            raise RuntimeError(j["error"].get("message", "rpc error"))
        return j["result"]


# ---- Redis rate limit ----
async def _rate_limit_sendraw(request: Request, x_guardian_key: str | None):
    # If REDIS_URL is not configured, we fail closed (safer) unless explicitly disabled.
    rl_enabled = (_env("RL_SENDRAW_ENABLED", "1") != "0")
    if not rl_enabled:
        return

    if not REDIS_URL:
        raise HTTPException(status_code=500, detail="REDIS_URL not set (rate limit enabled)")

    try:
        import redis.asyncio as redis  # type: ignore
    except Exception:
        raise HTTPException(status_code=500, detail="redis package missing (pip install redis)")

    now = int(time.time())
    minute = now // 60
    retry_after = 60 - (now % 60)

    ip = _client_ip(request)
    kid = _kid_from_key(x_guardian_key)

    k_ip = f"rl:sendraw:{ip}:{minute}"
    k_key = f"rl:sendraw:key:{kid}:{minute}"

    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        pipe = r.pipeline()
        pipe.incr(k_ip)
        pipe.expire(k_ip, RL_TTL_SEC)
        pipe.incr(k_key)
        pipe.expire(k_key, RL_TTL_SEC)
        ip_count, _, key_count, _ = await pipe.execute()

        if int(ip_count) > RL_IP_PER_MIN or int(key_count) > RL_KEY_PER_MIN:
            # 429 with Retry-After
            headers = {"Retry-After": str(retry_after)}
            return JSONResponse(
                status_code=429,
                content={"detail": "rate_limited", "retry_after": retry_after},
                headers=headers,
            )
    finally:
        try:
            await r.aclose()
        except Exception:
            pass

    return None


# ---- RLP decode (minimal) for legacy tx only ----
def _rlp_decode_item(buf: bytes, i: int = 0):
    if i >= len(buf):
        raise ValueError("rlp: out of range")
    b0 = buf[i]
    if b0 <= 0x7F:
        return buf[i : i + 1], i + 1
    if b0 <= 0xB7:
        l = b0 - 0x80
        if l == 0:
            return b"", i + 1
        return buf[i + 1 : i + 1 + l], i + 1 + l
    if b0 <= 0xBF:
        ll = b0 - 0xB7
        l = int.from_bytes(buf[i + 1 : i + 1 + ll], "big")
        start = i + 1 + ll
        return buf[start : start + l], start + l
    if b0 <= 0xF7:
        l = b0 - 0xC0
        items = []
        j = i + 1
        end = j + l
        while j < end:
            it, j = _rlp_decode_item(buf, j)
            items.append(it)
        return items, j
    ll = b0 - 0xF7
    l = int.from_bytes(buf[i + 1 : i + 1 + ll], "big")
    j = i + 1 + ll
    end = j + l
    items = []
    while j < end:
        it, j = _rlp_decode_item(buf, j)
        items.append(it)
    return items, j


def _decode_legacy_tx(raw_hex: str) -> dict:
    raw_hex = raw_hex.strip()
    if raw_hex.startswith("0x"):
        raw_hex = raw_hex[2:]
    b = bytes.fromhex(raw_hex)
    decoded, _ = _rlp_decode_item(b, 0)
    if not isinstance(decoded, list) or len(decoded) < 9:
        raise ValueError("not legacy tx rlp list")

    # [nonce, gasPrice, gas, to, value, data, v, r, s]
    def bi(x: bytes) -> int:
        return int.from_bytes(x, "big") if x else 0

    to_b = decoded[3]
    to_addr = ("0x" + to_b.hex()) if to_b else "0x"
    data_b = decoded[5] if len(decoded) > 5 else b""
    v = bi(decoded[6])

    chain_id = None
    if v >= 35:
        chain_id = (v - 35) // 2

    return {
        "to": to_addr.lower(),
        "data": ("0x" + data_b.hex()) if data_b else "0x",
        "chainId": chain_id,
    }


def _extract_transfer_amount(data_hex: str) -> Optional[int]:
    if not data_hex or not data_hex.startswith("0x"):
        return None
    if not data_hex.startswith(TRANSFER_SELECTOR):
        return None
    hx = data_hex[2:]
    if len(hx) < 8 + 64 + 64:
        return None
    amt_hex = hx[8 + 64 : 8 + 64 + 64]
    return int(amt_hex, 16)


class SendRawIn(BaseModel):
    rawTx: str | None = None
    raw_tx: str | None = None
    note: str | None = None

    def pick_raw(self) -> str:
        return (self.rawTx or self.raw_tx or "").strip()


class ReceiptIn(BaseModel):
    tx_hash: str


@router.post("/sendRaw")
async def send_raw_tx(
    body: SendRawIn,
    request: Request,
    x_guardian_key: str | None = Header(default=None),
):
    _require_internal_key(x_guardian_key)

    # Rate limit (Redis)
    limited = await _rate_limit_sendraw(request, x_guardian_key)
    if limited is not None:
        return limited

    raw = body.pick_raw()
    if not _is_hex_tx(raw) or len(raw) < 10 or not raw.startswith("0x"):
        raise HTTPException(status_code=400, detail="rawTx must be hex string starting with 0x")

    # Decode & enforce policy (legacy tx only for now)
    try:
        info = _decode_legacy_tx(raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"rawTx decode failed: {type(e).__name__}")

    # enforce chainId=56 if present
    if info.get("chainId") is not None and int(info["chainId"]) != 56:
        raise HTTPException(status_code=403, detail=f"chainId not allowed: {info.get('chainId')}")

    # enforce token allowlist on tx.to (token contract)
    allow = _token_allowlist()
    if not allow:
        raise HTTPException(status_code=500, detail="GUARDIAN_TOKEN_ALLOWLIST empty")
    if info["to"] not in allow:
        raise HTTPException(status_code=403, detail=f"tx.to not allowed: {info['to']}")

    # enforce ERC20 transfer selector and optional max amount
    data = info.get("data", "0x")
    if not data.startswith(TRANSFER_SELECTOR):
        raise HTTPException(status_code=403, detail="only ERC20 transfer allowed")

    max_amt_raw = _env("MAX_AMOUNT_RAW", "")
    if max_amt_raw:
        try:
            mx = int(max_amt_raw)
            amt = _extract_transfer_amount(data)
            if amt is not None and amt > mx:
                raise HTTPException(status_code=403, detail="amount exceeds MAX_AMOUNT_RAW")
        except ValueError:
            pass

    # broadcast
    try:
        txh = await _rpc("eth_sendRawTransaction", [raw])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"rpc broadcast failed: {type(e).__name__}: {str(e)}")

    return {"ok": True, "tx_hash": txh}


@router.post("/receipt")
async def receipt(
    body: ReceiptIn,
    x_guardian_key: str | None = Header(default=None),
):
    _require_internal_key(x_guardian_key)

    txh = (body.tx_hash or "").strip()
    if not _is_hexhash(txh):
        raise HTTPException(status_code=400, detail="tx_hash must be 0x + 64 hex chars")

    try:
        rcpt = await _rpc("eth_getTransactionReceipt", [txh])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"rpc receipt failed: {type(e).__name__}")

    if rcpt is None:
        return {"ok": True, "found": False, "tx_hash": txh}

    to_addr = (rcpt.get("to") or "").lower()

    # enforce allowlist on receipt to address (token contract)
    allow = _token_allowlist()
    if allow and to_addr and (to_addr not in allow):
        raise HTTPException(status_code=403, detail=f"receipt to-address not allowed: {to_addr}")

    transfers = []
    for lg in (rcpt.get("logs") or []):
        if (lg.get("address", "").lower() != to_addr):
            continue
        topics = lg.get("topics") or []
        if len(topics) >= 3 and (topics[0].lower() == TRANSFER_TOPIC0):
            frm = "0x" + topics[1][-40:]
            to = "0x" + topics[2][-40:]
            data = lg.get("data", "0x0")
            transfers.append({"from": frm, "to": to, "value_hex": data})

    return {
        "ok": True,
        "found": True,
        "status": rcpt.get("status"),
        "from": rcpt.get("from"),
        "to": rcpt.get("to"),
        "blockNumber": rcpt.get("blockNumber"),
        "gasUsed": rcpt.get("gasUsed"),
        "effectiveGasPrice": rcpt.get("effectiveGasPrice"),
        "transfers": transfers,
        "tx_hash": txh,
    }