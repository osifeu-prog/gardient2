from pathlib import Path
import re

f = Path("migrations/versions/de19e92ebfed_init_saas_core.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# Replace drop_table('X'...) -> op.execute("DROP TABLE IF EXISTS X CASCADE")
def repl_drop_table(m):
    name = m.group(1)
    return f"op.execute(\"DROP TABLE IF EXISTS {name} CASCADE\")"

# Replace drop_index('IDX', table_name='TBL'...) -> op.execute("DROP INDEX IF EXISTS IDX")
def repl_drop_index(m):
    idx = m.group(1)
    return f"op.execute(\"DROP INDEX IF EXISTS {idx}\")"

s2, n_tables = re.subn(r"op\.drop_table\(\s*['\"]([a-zA-Z0-9_]+)['\"][^\)]*\)", repl_drop_table, s)
s3, n_idx = re.subn(r"op\.drop_index\(\s*['\"]([a-zA-Z0-9_]+)['\"][^\)]*\)", repl_drop_index, s2)

if n_tables == 0 and n_idx == 0:
    raise SystemExit("ERROR: nothing patched")

f.write_text(s3, encoding="utf-8")
print(f"OK: patched {f.name} drop_table={n_tables} drop_index={n_idx}")
