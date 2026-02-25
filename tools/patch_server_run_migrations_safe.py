from pathlib import Path
import re

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# add import
if "run_migrations_safe" not in s:
    s = s.replace(
        "from bot.infrastructure import init_infrastructure",
        "from bot.infrastructure import init_infrastructure, run_migrations_safe"
    )

# call it in lifespan right after init_infrastructure
pat = r"await init_infrastructure\(\)\n"
if re.search(pat, s) and "await run_migrations_safe()" not in s:
    s = re.sub(pat, "await init_infrastructure()\n    await run_migrations_safe()\n", s, count=1)

p.write_text(s, encoding="utf-8")
print("OK: patched bot/server.py to run migrations on startup (safe)")
