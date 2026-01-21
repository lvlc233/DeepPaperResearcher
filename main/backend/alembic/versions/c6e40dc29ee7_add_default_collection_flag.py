"""add_default_collection_flag

Revision ID: c6e40dc29ee7
Revises: 555e29c4540c
Create Date: 2026-01-17 12:06:59.880303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import pgvector


# revision identifiers, used by Alembic.
revision: str = 'c6e40dc29ee7'
down_revision: Union[str, Sequence[str], None] = '555e29c4540c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'collections',
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false(), comment='是否为默认收藏夹')
    )
    op.create_index(op.f('ix_collections_is_default'), 'collections', ['is_default'], unique=False)
    op.create_index(
        'uq_collections_user_default',
        'collections',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text('is_default')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_collections_user_default', table_name='collections')
    op.drop_index(op.f('ix_collections_is_default'), table_name='collections')
    op.drop_column('collections', 'is_default')
