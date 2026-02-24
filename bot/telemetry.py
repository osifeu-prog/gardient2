import json
import logging
import time
import traceback
from typing import Any, Dict

LOGGER_NAME = "guardian"
logger = logging.getLogger(LOGGER_NAME)

def now_ms() -> int:
    return int(time.time() * 1000)

def log_json(level: int, event: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {"ts_ms": now_ms(), "event": event, **fields}
    msg = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    logger.log(level, msg)

def exc_to_str(e: BaseException) -> str:
    return "".join(traceback.format_exception(type(e), e, e.__traceback__)).strip()

def update_brief(update: Any) -> Dict[str, Any]:
    try:
        u = getattr(update, "effective_user", None)
        c = getattr(update, "effective_chat", None)
        m = getattr(update, "effective_message", None)
        txt = getattr(m, "text", None) if m else None
        return {
            "chat_id": getattr(c, "id", None),
            "user_id": getattr(u, "id", None),
            "username": getattr(u, "username", None),
            "text": (txt[:120] if isinstance(txt, str) else None),
        }
    except Exception:
        return {}
