from pathlib import Path
import re

f = Path("migrations/versions/de19e92ebfed_init_saas_core.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# 1) Ensure users table exists early in upgrade()
# Insert right after "def upgrade():" line
marker = "def upgrade():"
if marker not in s:
    raise SystemExit("ERROR: upgrade() not found")

create_users_sql = """    # Safety: ensure base users table exists (db may start empty)
    op.execute("CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, created_at TIMESTAMPTZ DEFAULT now())")
"""

if create_users_sql.strip() not in s:
    s = s.replace(marker, marker + "\n" + create_users_sql, 1)

# 2) Make users column drops safe: op.drop_column('users','x') -> ALTER TABLE IF EXISTS users DROP COLUMN IF EXISTS x
def repl_drop_col(m):
    col = m.group(1)
    return f'op.execute("ALTER TABLE IF EXISTS users DROP COLUMN IF EXISTS {col}")'

s, n_dropcols = re.subn(r"op\.drop_column\(\s*'users'\s*,\s*'([a-zA-Z0-9_]+)'\s*\)", repl_drop_col, s)

# 3) Make ix_users_email drop safe if exists
s = s.replace(
    "op.drop_index('ix_users_email', table_name='users')",
    "op.execute(\"DROP INDEX IF EXISTS ix_users_email\")"
)

# 4) Make add_column chat_id/username safe if run twice
s = s.replace(
    "op.add_column('users', sa.Column('chat_id', sa.BigInteger(), nullable=True))",
    "op.execute(\"ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS chat_id BIGINT\")"
)
s = s.replace(
    "op.add_column('users', sa.Column('username', sa.String(length=128), nullable=True))",
    "op.execute(\"ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS username VARCHAR(128)\")"
)

f.write_text(s, encoding="utf-8")
print(f"OK: patched de19 (dropcols_patched={n_dropcols})")
