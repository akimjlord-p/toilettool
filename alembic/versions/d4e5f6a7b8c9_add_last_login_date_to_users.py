"""add last_login_date to users

Revision ID: d4e5f6a7b8c9
Revises: c3f1d8a02e51
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3f1d8a02e51'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_login_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_login_date')
