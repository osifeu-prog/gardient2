from pathlib import Path
import re

p = Path("migrations/versions")
cands = sorted(p.glob("*_rbac_core.py"), key=lambda x: x.stat().st_mtime, reverse=True)
if not cands:
    raise SystemExit("ERROR: no *_rbac_core.py found in migrations/versions")

mf = cands[0]
s = mf.read_text(encoding="utf-8").replace("\r\n","\n")

# replace the permissions create_table block with correct schema
pattern = r'op\.create_table\(\s*"permissions"\s*,[\s\S]*?\)\s*\n'
replacement = """op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
"""

s2, n = re.subn(pattern, replacement, s, count=1)
if n != 1:
    raise SystemExit(f"ERROR: could not patch permissions table block in {mf.name}")

mf.write_text(s2, encoding="utf-8")
print("OK: patched", mf.as_posix())
