from pathlib import Path
import re

p = Path("bot/infrastructure.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# find candidates
funcs = re.findall(r'async def (\w+)\(', s)

pg = None
rd = None

# heuristic: prefer names containing postgres
for f in funcs:
    if "postgres" in f.lower():
        pg = f
        break

# heuristic: prefer names containing redis
for f in funcs:
    if "redis" in f.lower():
        rd = f
        break

if not pg or not rd:
    raise SystemExit(f"ERROR: could not detect postgres/redis check functions. Found={funcs}")

# remove old broken wrappers if present
s = re.sub(r'\nasync def check_postgres\([\s\S]*?\n', "\n", s, count=1)
s = re.sub(r'\nasync def check_redis\([\s\S]*?\n', "\n", s, count=1)

# append correct wrappers
s += f"""

async def check_postgres():
    # wrapper used by /readyz
    await {pg}()

async def check_redis():
    # wrapper used by /readyz
    await {rd}()
"""

p.write_text(s, encoding="utf-8")
print(f"OK: wrappers updated -> postgres:{pg} redis:{rd}")
