"""
Add is_admin field to user table

Revision ID: fc0849dbd942
Revises: a327c2520ffb
Create Date: 2025-12-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc0849dbd942'
down_revision: Union[str, Sequence[str], None] = 'a327c2520ffb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add is_admin field to user table."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.create_index('ix_user_is_admin', ['is_admin'])


def downgrade() -> None:
    """Downgrade schema: remove is_admin field from user table."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index('ix_user_is_admin')
        batch_op.drop_column('is_admin')
