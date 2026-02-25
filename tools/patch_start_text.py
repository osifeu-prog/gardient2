from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Insert donate/admins lines after the /health line in start_cmd text
pattern = r'("?/health\s+system health\\n")'
replacement = r'\1"        "/donate    support / donate\\n"\n        "/admins    list admins (access-controlled)\\n"'

s2, n = re.subn(pattern, replacement, s, count=1)
if n != 1:
    raise SystemExit("ERROR: could not patch start_cmd health line")

p.write_text(s2, encoding="utf-8")
print("OK: patched start_cmd to show donate/admins")
