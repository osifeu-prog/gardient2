from pathlib import Path
import re

p = Path("bot/main.py")
s = p.read_text(encoding="utf-8")

# Ensure Path import exists
if "from pathlib import Path" not in s:
    s = s.replace("import time\n", "import time\nfrom pathlib import Path\n", 1)

# Replace ASCII_BANNER block with file loader + fallback
replacement = '''ASCII_BANNER = ""
try:
    ASCII_BANNER = Path("assets/banner.txt").read_text(encoding="utf-8")
except Exception:
    ASCII_BANNER = r"""
=====================================
==           SLH  GUARDIAN          ==
=====================================
"""
'''

s, n = re.subn(r'ASCII_BANNER\s*=\s*r?"""\s*[\s\S]*?\s*"""', replacement, s, count=1)
if n == 0:
    raise SystemExit("ERROR: ASCII_BANNER block not found")

p.write_text(s, encoding="utf-8", newline="\n")
print("OK: patched bot/main.py (banner from assets/banner.txt)")
