"""add review_photos table

Revision ID: b9a299206f4d
Revises: 2bb6312a5c9f
Create Date: 2026-06-10 09:36:58.324783

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'b9a299206f4d'
down_revision: Union[str, None] = '2bb6312a5c9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'review_photos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('review_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_id', sa.String(255), nullable=False),
        sa.Column('position', sa.SmallInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['review_id'], ['reviews.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_review_photos_review_id', 'review_photos', ['review_id'])

def downgrade() -> None:
    op.drop_index('ix_review_photos_review_id', table_name='review_photos')
    op.drop_table('review_photos')
