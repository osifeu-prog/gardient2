from pathlib import Path
import re

f = Path("migrations/versions/de19e92ebfed_init_saas_core.py")
s = f.read_text(encoding="utf-8").replace("\r\n","\n")

# Insert safety SQL right before the first occurrence of any "op.add_column('users'" or "op.alter_column('users'"
m = re.search(r"(?m)^\s*op\.(add_column|alter_column)\(\s*'users'", s)
if not m:
    raise SystemExit("ERROR: could not find first users op.* call to anchor insertion")

anchor_pos = m.start()

injection = (
    "    # Safety: ensure users table exists on empty DB\n"
    "    op.execute(\"CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, created_at TIMESTAMPTZ DEFAULT now())\")\n"
)

# Ensure we only inject once
if "CREATE TABLE IF NOT EXISTS users" not in s:
    s2 = s[:anchor_pos] + injection + s[anchor_pos:]
else:
    s2 = s

# Also make add_column chat_id/username safe regardless of table existence
s2 = s2.replace(
    "op.add_column('users', sa.Column('chat_id', sa.BigInteger(), nullable=True))",
    "op.execute(\"ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS chat_id BIGINT\")"
)
s2 = s2.replace(
    "op.add_column('users', sa.Column('username', sa.String(length=128), nullable=True))",
    "op.execute(\"ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS username VARCHAR(128)\")"
)

f.write_text(s2, encoding="utf-8")
print("OK: injected users CREATE TABLE before first users op + made chat_id/username safe")
