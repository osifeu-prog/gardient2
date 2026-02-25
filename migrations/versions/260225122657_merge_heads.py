"""merge heads

Revision ID: 260225122657
Revises: 260225114018, de19e92ebfed
Create Date: 2026-02-25T12:26:57.989627Z
"""

from alembic import op

revision = "260225122657"
down_revision = ('260225114018', 'de19e92ebfed')
branch_labels = None
depends_on = None

def upgrade():
    # merge-only migration (no-op)
    pass

def downgrade():
    # cannot reliably downgrade a merge without choosing a branch
    pass
