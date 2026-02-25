from pathlib import Path
import re

f = Path("migrations/versions/de19e92ebfed_init_saas_core.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# Patch op.drop_index('ix_manh_invoices_user', table_name='manh_invoices')
# -> op.drop_index('ix_manh_invoices_user', table_name='manh_invoices', if_exists=True)

pattern = r"op\.drop_index\(\s*['\"]ix_manh_invoices_user['\"]\s*,\s*table_name\s*=\s*['\"]manh_invoices['\"]\s*\)"
replacement = "op.drop_index('ix_manh_invoices_user', table_name='manh_invoices', if_exists=True)"

s2, n = re.subn(pattern, replacement, s, count=1)
if n != 1:
    raise SystemExit(f"ERROR: expected to patch exactly 1 drop_index; patched={n}")

f.write_text(s2, encoding="utf-8")
print("OK: patched drop_index to if_exists=True in", f.name)
