"""
Add promo code table

Revision ID: 229e0177563b
Revises: fc0849dbd942
Create Date: 2025-12-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '229e0177563b'
down_revision: Union[str, Sequence[str], None] = 'fc0849dbd942'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add promo code table."""
    # Check if table already exists (in case it was created manually)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'promocode' not in tables:
        op.create_table(
            'promocode',
            sa.Column('id', sa.Uuid(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(), nullable=False,
                      unique=True, index=True),
            sa.Column('plan', sa.String(), nullable=False, index=True),
            sa.Column('created_by', sa.Uuid(), sa.ForeignKey(
                'user.id'), nullable=False, index=True),
            sa.Column('used_by', sa.Uuid(), sa.ForeignKey(
                'user.id'), nullable=True, index=True),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('is_used', sa.Boolean(), nullable=False,
                      server_default='0', index=True),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
        )
    else:
        # Table exists, but we need to ensure indexes exist
        # Check and create indexes if they don't exist
        indexes = [idx['name'] for idx in inspector.get_indexes('promocode')]

        if 'ix_promocode_code' not in indexes:
            op.create_index('ix_promocode_code', 'promocode',
                            ['code'], unique=True)
        if 'ix_promocode_plan' not in indexes:
            op.create_index('ix_promocode_plan', 'promocode', ['plan'])
        if 'ix_promocode_created_by' not in indexes:
            op.create_index('ix_promocode_created_by',
                            'promocode', ['created_by'])
        if 'ix_promocode_used_by' not in indexes:
            op.create_index('ix_promocode_used_by', 'promocode', ['used_by'])
        if 'ix_promocode_is_used' not in indexes:
            op.create_index('ix_promocode_is_used', 'promocode', ['is_used'])


def downgrade() -> None:
    """Downgrade schema: drop promo code table."""
    op.drop_table('promocode')
