from pathlib import Path
import re

f = Path("migrations/versions/de19e92ebfed_init_saas_core.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# Patch drop_table('manh_invoices') -> drop_table('manh_invoices', if_exists=True)
# handle both single and double quotes
s2, n = re.subn(r"op\.drop_table\(\s*['\"]manh_invoices['\"]\s*\)", "op.drop_table('manh_invoices', if_exists=True)", s)

if n < 1:
    raise SystemExit("ERROR: could not find op.drop_table('manh_invoices') to patch")

f.write_text(s2, encoding="utf-8")
print("OK: patched drop_table manh_invoices if_exists=True (count=%d)" % n)
