from pathlib import Path
import re

p = Path("bot/infrastructure.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

s = re.sub(r'\nasync def check_postgres\([\s\S]*?\n', "\n", s, count=1)
s = re.sub(r'\nasync def check_redis\([\s\S]*?\n', "\n", s, count=1)

p.write_text(s, encoding="utf-8")
print("OK: removed check_postgres/check_redis wrappers")
