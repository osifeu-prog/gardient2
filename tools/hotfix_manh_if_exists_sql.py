from pathlib import Path
import re

f = Path("migrations/versions/de19e92ebfed_init_saas_core.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# Replace drop_table('manh_invoices', ...) with raw SQL IF EXISTS
s2, n1 = re.subn(
    r"op\.drop_table\(\s*['\"]manh_invoices['\"][^\)]*\)",
    "op.execute('DROP TABLE IF EXISTS manh_invoices CASCADE')",
    s
)

# Replace drop_index('ix_manh_invoices_user', table_name='manh_invoices', ...) with raw SQL IF EXISTS
s3, n2 = re.subn(
    r"op\.drop_index\(\s*['\"]ix_manh_invoices_user['\"][^\)]*\)",
    "op.execute('DROP INDEX IF EXISTS ix_manh_invoices_user')",
    s2
)

if n1 < 1 and n2 < 1:
    raise SystemExit("ERROR: did not patch anything (patterns not found)")

f.write_text(s3, encoding="utf-8")
print(f\"OK: patched de19e92ebfed_init_saas_core.py (drop_table patches={n1}, drop_index patches={n2})\")
