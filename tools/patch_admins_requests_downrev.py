from pathlib import Path
import re

f = Path("migrations/versions/admins_requests_20260225_010837.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure revision line exists; ensure down_revision points to de19e92ebfed
# 1) If down_revision is None or empty, set it.
s = re.sub(r'(?m)^down_revision\s*=\s*None\s*$', "down_revision = 'de19e92ebfed'", s)
s = re.sub(r"(?m)^down_revision\s*=\s*['\"]\s*['\"]\s*$", "down_revision = 'de19e92ebfed'", s)

# 2) If it's missing entirely, insert after revision=
if not re.search(r"(?m)^down_revision\s*=", s):
    s = re.sub(
        r"(?m)^(revision\s*=\s*['\"][^'\"]+['\"]\s*)$",
        r"\1\ndown_revision = 'de19e92ebfed'",
        s,
        count=1
    )

f.write_text(s, encoding="utf-8")
print("OK: patched down_revision in", f.name)
