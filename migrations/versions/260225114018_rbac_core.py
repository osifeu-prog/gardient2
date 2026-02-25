"""rbac core

Revision ID: 260225114018
Revises: None
Create Date: 2026-02-25T11:40:18.169082Z
"""

from alembic import op
import sqlalchemy as sa

revision = "260225114018"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Integer, sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.BigInteger, nullable=False),  # telegram user id
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_by", sa.BigInteger, nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # Seed minimal roles (owner/admin) and a few perms (extensible)
    op.execute("INSERT INTO roles(name, description) VALUES ('owner','System owner'), ('admin','System admin') ON CONFLICT DO NOTHING;")
    op.execute("INSERT INTO permissions(name, description) VALUES "
               "('admin.manage','Manage admins'),"
               "('admin.dm','DM users'),"
               "('admin.broadcast','Broadcast admins'),"
               "('payments.view','View payment links')"
               " ON CONFLICT DO NOTHING;")
    op.execute("INSERT INTO role_permissions(role_id, permission_id) "
               "SELECT r.id, p.id FROM roles r, permissions p "
               "WHERE r.name='owner' "
               "ON CONFLICT DO NOTHING;")
    op.execute("INSERT INTO role_permissions(role_id, permission_id) "
               "SELECT r.id, p.id FROM roles r, permissions p "
               "WHERE r.name='admin' AND p.name IN ('admin.dm','admin.broadcast') "
               "ON CONFLICT DO NOTHING;")


def downgrade():
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
