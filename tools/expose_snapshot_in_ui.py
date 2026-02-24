from pathlib import Path

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Add /snapshot line to start admin text (only if not present)
if "/snapshot" not in s:
    s = s.replace(
        "/pingredis Redis latency\\n",
        "/pingredis Redis latency\\n"
        "/snapshot  snapshot\\n",
        1
    )

# Add /snapshot to menu admin list (best-effort, only if missing)
needle = 'lines += ["", "Admin:", "/admin", "/vars", "/webhook", "/diag", "/pingdb", "/pingredis"]'
if needle in s and "/snapshot" not in s:
    s = s.replace(needle, needle[:-1] + ', "/snapshot"]', 1)

p.write_text(s, encoding="utf-8")
print("OK: /snapshot exposed in /start and /menu")
