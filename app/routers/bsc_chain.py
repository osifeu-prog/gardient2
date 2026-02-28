from fastapi import APIRouter, Query, HTTPException
import httpx
from typing import Any

router = APIRouter(prefix="/chain/bsc", tags=["chain-bsc"])

RPC = "https://bsc-dataseed.binance.org/"
TOKEN = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"

def _addr32(addr: str) -> str:
    a = addr.lower().replace("0x","")
    if len(a) != 40:
        raise ValueError("invalid address length")
    return a.rjust(64, "0")

async def _eth_call(data: str) -> str:
    payload = {"jsonrpc":"2.0","method":"eth_call","params":[{"to":TOKEN,"data":data},"latest"],"id":1}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(RPC, json=payload)
        r.raise_for_status()
        j = r.json()
        if "error" in j:
            raise RuntimeError(j["error"].get("message","rpc error"))
        return j["result"]

def _hex_to_int(h: str) -> int:
    return int(h, 16)

def _format_units(x: int, dec: int) -> str:
    s = str(x)
    if dec <= 0:
        return s
    if len(s) <= dec:
        s = "0" * (dec - len(s) + 1) + s
    i = s[:-dec]
    f = s[-dec:].rstrip("0")
    return i if not f else f"{i}.{f}"

@router.get("/token-meta")
async def token_meta() -> dict[str, Any]:
    try:
        decimals_hex = await _eth_call("0x313ce567")
        total_hex    = await _eth_call("0x18160ddd")
        owner_hex    = await _eth_call("0x8da5cb5b")
        dec = _hex_to_int(decimals_hex)
        total = _hex_to_int(total_hex)
        owner = "0x" + owner_hex[-40:]
        return {"token": TOKEN, "decimals": dec, "totalSupply": _format_units(total, dec), "owner": owner}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance")
async def balance(addr: str = Query(..., description="0x...")) -> dict[str, Any]:
    try:
        dec_hex = await _eth_call("0x313ce567")
        dec = _hex_to_int(dec_hex)
        data = "0x70a08231" + _addr32(addr)
        bal_hex = await _eth_call(data)
        bal = _hex_to_int(bal_hex)
        return {"addr": addr, "token": TOKEN, "balance": _format_units(bal, dec), "decimals": dec}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
