"""add balance to users

Revision ID: c3f1d8a02e51
Revises: b9a299206f4d
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3f1d8a02e51'
down_revision = 'b9a299206f4d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('balance', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'balance')
