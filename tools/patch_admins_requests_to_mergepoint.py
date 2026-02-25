from pathlib import Path
import re

f = Path("migrations/versions/admins_requests_20260225_010837.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")
s2 = re.sub(r"(?m)^down_revision\s*=\s*['\"][^'\"]+['\"]\s*$", "down_revision = '260225122657'", s)
if s2 == s:
    # if line missing
    if not re.search(r"(?m)^down_revision\s*=", s):
        s2 = re.sub(r"(?m)^(revision\s*=\s*['\"][^'\"]+['\"]\s*)$", r"\1\ndown_revision = '260225122657'", s, count=1)
    else:
        s2 = s
f.write_text(s2, encoding="utf-8")
print("OK: admins_requests now depends on 260225122657")
