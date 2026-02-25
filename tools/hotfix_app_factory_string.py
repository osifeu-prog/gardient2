from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Fix the broken concatenation introduced by bad patch:
# ... "/health    system health\n""        "/donate ...
s2 = s.replace(
    '"/health    system health\\n""        "/donate    support / donate\\n"',
    '"/health    system health\\n"\n        "/donate    support / donate\\n"'
)

# Also fix if admins line got broken similarly
s2 = s2.replace(
    '"/donate    support / donate\\n""        "/admins    list admins (access-controlled)\\n"',
    '"/donate    support / donate\\n"\n        "/admins    list admins (access-controlled)\\n"'
)

# If still contains the bad pattern, hard fail
if 'system health\\n""' in s2:
    raise SystemExit("ERROR: still contains broken string pattern system health\\\\n\\\"\\\"")

p.write_text(s2, encoding="utf-8")
print("OK: hotfixed app_factory.py string concatenation")
