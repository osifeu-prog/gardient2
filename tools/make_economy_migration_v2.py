import re, subprocess
from pathlib import Path
from datetime import datetime

VERS = Path("migrations/versions")
VERS.mkdir(parents=True, exist_ok=True)

# heads output example: "admins_requests_20260225_010837 (head)"
heads_out = subprocess.check_output(["py","-m","alembic","heads"], text=True, stderr=subprocess.STDOUT)
m = re.search(r"^([A-Za-z0-9_]+)\s+\(head\)", heads_out, flags=re.M)
down = m.group(1) if m else None
if not down:
    raise SystemExit("ERROR: could not detect alembic head. output:\n" + heads_out)

rev = datetime.utcnow().strftime("%y%m%d%H%M%S")
path = VERS / f"{rev}_economy_core.py"

content = f'''"""economy core

Revision ID: {rev}
Revises: {down}
Create Date: {datetime.utcnow().isoformat()}Z
"""

from alembic import op
import sqlalchemy as sa

revision = "{rev}"
down_revision = "{down}"
branch_labels = None
depends_on = None


def upgrade():
    # Plans / pricing
    op.create_table(
        "plans",
        sa.Column("code", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("price_amount", sa.Integer, nullable=False),
        sa.Column("price_currency", sa.String(length=16), nullable=False, server_default="SELHA"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Manual requests (buy/donate)
    op.create_table(
        "payment_requests",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),  # donate|buy_token
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False, server_default="SELHA"),
        sa.Column("tx_ref", sa.String(length=256), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("decided_by", sa.BigInteger, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_payment_requests_status", "payment_requests", ["status"], unique=False)
    op.create_index("ix_payment_requests_user", "payment_requests", ["user_id", "created_at"], unique=False)

    # Internal points ledger (SELHA)
    op.create_table(
        "points_ledger",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("delta", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),  # donate|buy_token|admin_adjust
        sa.Column("ref", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_points_ledger_user", "points_ledger", ["user_id", "created_at"], unique=False)

    # Referrals
    op.create_table(
        "referrals",
        sa.Column("referrer_id", sa.BigInteger, nullable=False),
        sa.Column("referred_id", sa.BigInteger, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("referrer_id", "referred_id"),
    )

    # Accounts (bank/crypto)
    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),  # bank|crypto
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("details_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_accounts_user", "accounts", ["user_id", "created_at"], unique=False)

    # Seed a default plan
    op.execute("INSERT INTO plans(code,name,price_amount,price_currency,is_active) VALUES ('token_basic','Token Basic',100,'SELHA',true) ON CONFLICT DO NOTHING;")


def downgrade():
    op.drop_index("ix_accounts_user", table_name="accounts")
    op.drop_table("accounts")
    op.drop_table("referrals")
    op.drop_index("ix_points_ledger_user", table_name="points_ledger")
    op.drop_table("points_ledger")
    op.drop_index("ix_payment_requests_user", table_name="payment_requests")
    op.drop_index("ix_payment_requests_status", table_name="payment_requests")
    op.drop_table("payment_requests")
    op.drop_table("plans")
'''
path.write_text(content.replace("\r\n","\n"), encoding="utf-8")
print("OK:", path.as_posix())
print("DOWN_REV:", down)
