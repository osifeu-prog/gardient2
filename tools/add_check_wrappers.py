from pathlib import Path
import re

p = Path("bot/infrastructure.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Add two helpers if missing
if "async def check_postgres" not in s:
    s += "\n\nasync def check_postgres():\n    # used by /readyz for latency measurement\n    await _check_postgres()\n"
if "async def check_redis" not in s:
    s += "\n\nasync def check_redis():\n    # used by /readyz for latency measurement\n    await _check_redis()\n"

p.write_text(s, encoding="utf-8")
print("OK: added check_postgres/check_redis wrappers")
