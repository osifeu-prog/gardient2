import re
import subprocess
from pathlib import Path
from datetime import datetime

def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)

out = run(["py", "-m", "alembic", "heads"])
heads = re.findall(r"^([0-9a-f]+)\s+\(head\)", out, flags=re.M)
heads = list(dict.fromkeys(heads))

if len(heads) < 2:
    raise SystemExit("ERROR: expected multiple heads; got: " + str(heads))

rev = datetime.utcnow().strftime("%y%m%d%H%M%S")
fname = f"{rev}_merge_heads.py"
path = Path("migrations/versions") / fname

content = f'''"""merge heads

Revision ID: {rev}
Revises: {", ".join(heads)}
Create Date: {datetime.utcnow().isoformat()}Z
"""

from alembic import op

revision = "{rev}"
down_revision = ({", ".join([repr(h) for h in heads])})
branch_labels = None
depends_on = None

def upgrade():
    # merge-only migration (no-op)
    pass

def downgrade():
    # cannot reliably downgrade a merge without choosing a branch
    pass
'''
path.write_text(content.replace("\r\n","\n"), encoding="utf-8")
print("OK: wrote", path.as_posix())
print("MERGED HEADS:", heads)
