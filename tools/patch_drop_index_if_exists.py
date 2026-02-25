from pathlib import Path
import re

files = list(Path("migrations/versions").glob("*.py"))
targets = []
for f in files:
    s = f.read_text(encoding="utf-8", errors="ignore")
    if "ix_manh_invoices_user" in s and "DROP INDEX" in s:
        targets.append(f)

if not targets:
    raise SystemExit("ERROR: could not find migration referencing ix_manh_invoices_user")

for f in targets:
    s = f.read_text(encoding="utf-8").replace("\r\n","\n")
    s2 = s

    # Replace raw DROP INDEX with safe IF EXISTS
    s2 = re.sub(r"DROP INDEX\s+ix_manh_invoices_user\s*;?", "DROP INDEX IF EXISTS ix_manh_invoices_user;", s2)

    # Also handle op.execute("DROP INDEX ...")
    s2 = s2.replace('op.execute("DROP INDEX ix_manh_invoices_user")', 'op.execute("DROP INDEX IF EXISTS ix_manh_invoices_user")')
    s2 = s2.replace("op.execute('DROP INDEX ix_manh_invoices_user')", "op.execute('DROP INDEX IF EXISTS ix_manh_invoices_user')")

    if s2 != s:
        f.write_text(s2, encoding="utf-8")
        print("OK: patched", f.name)
    else:
        print("WARN: no change", f.name)

print("DONE")
