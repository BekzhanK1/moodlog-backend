"""

Revision ID: 1a2b3c4d5e6f
Revises: c4e50d898bde
Create Date: 2025-11-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = 'c4e50d898bde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add insight table."""
    op.create_table(
        'insight',
        sa.Column('id', sa.Uuid(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey(
            'user.id'), nullable=False, index=True),
        sa.Column('type', sa.String(length=32), nullable=False, index=True),
        sa.Column('period_key', sa.String(length=64),
                  nullable=False, index=True),
        sa.Column('period_label', sa.String(length=128), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('encrypted_content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
    )
    # Optional uniqueness: one insight per user/type/period
    op.create_unique_constraint(
        "uq_insight_user_type_period",
        "insight",
        ["user_id", "type", "period_key"],
    )


def downgrade() -> None:
    """Downgrade schema: drop insight table."""
    op.drop_constraint("uq_insight_user_type_period",
                       "insight", type_="unique")
    op.drop_table('insight')
