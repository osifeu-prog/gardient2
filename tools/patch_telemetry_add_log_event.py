from pathlib import Path
import re

p = Path("bot/telemetry.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

if "def log_event(" not in s:
    # append helper at end
    s += """

def log_event(level: int, event: str, **fields):
    # canonical structured log (one-line JSON)
    try:
        log_json(level, event, **fields)
    except Exception:
        # last resort fallback
        import logging as _logging
        _logging.getLogger("telemetry").log(level, f"{event} {fields}")
"""

p.write_text(s, encoding="utf-8")
print("OK: added log_event() to bot/telemetry.py")
