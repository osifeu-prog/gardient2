from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Add /snapshot to the start_cmd admin text block if missing
if "/snapshot" not in s:
    s = s.replace(
        "/pingredis Redis latency\\n",
        "/pingredis Redis latency\\n"
        "/snapshot  snapshot\\n",
        1
    )

# Add /snapshot to menu admin list if missing
s = s.replace(
    'lines += ["", "Admin:", "/admin", "/vars", "/webhook", "/diag", "/pingdb", "/pingredis"]',
    'lines += ["", "Admin:", "/admin", "/vars", "/webhook", "/diag", "/pingdb", "/pingredis", "/snapshot"]'
)

p.write_text(s, encoding="utf-8")
print("OK: /snapshot added to /start and /menu listings")
