\"\"\"admin tables

Revision ID: admins_requests_20260225_010359
Revises: 
Create Date: 2026-02-25 01:03:59

\"\"\"

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "admins_requests_20260225_010359"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "admins",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("added_by", sa.BigInteger(), nullable=True),
        sa.Column("added_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "admin_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_admin_requests_status", "admin_requests", ["status"])

def downgrade():
    op.drop_index("ix_admin_requests_status", table_name="admin_requests")
    op.drop_table("admin_requests")
    op.drop_table("admins")
