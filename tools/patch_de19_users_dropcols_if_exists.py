from pathlib import Path
import re

f = Path("migrations/versions/de19e92ebfed_init_saas_core.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# Replace: op.drop_column('users','X')  -->  op.execute("ALTER TABLE IF EXISTS users DROP COLUMN IF EXISTS X")
def repl(m):
    col = m.group(1)
    return f'op.execute("ALTER TABLE IF EXISTS users DROP COLUMN IF EXISTS {col}")'

s2, n = re.subn(r"op\.drop_column\(\s*'users'\s*,\s*'([a-zA-Z0-9_]+)'\s*\)", repl, s)

# Also make users index drop safe
s2 = s2.replace("op.drop_index('ix_users_email', table_name='users')", 'op.execute("DROP INDEX IF EXISTS ix_users_email")')

f.write_text(s2, encoding="utf-8")
print(f"OK: patched users drop_column count={n}")
