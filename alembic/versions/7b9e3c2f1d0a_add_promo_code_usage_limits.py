"""add promo code usage limits

Revision ID: 7b9e3c2f1d0a
Revises: 229e0177563b
Create Date: 2025-12-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b9e3c2f1d0a"
# Place this migration after the latest existing head to keep a linear history.
down_revision: Union[str, Sequence[str], None] = "4d07f5e05a65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add usage limits to promo codes."""
    # Add new columns with safe defaults so existing codes behave as one-time
    op.add_column(
        "promocode",
        sa.Column(
            "max_uses",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "promocode",
        sa.Column(
            "uses_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Ensure existing rows have max_uses = 1 (one-time) and uses_count = 0
    op.execute("UPDATE promocode SET max_uses = 1 WHERE max_uses IS NULL")
    op.execute("UPDATE promocode SET uses_count = 0 WHERE uses_count IS NULL")


def downgrade() -> None:
    """Downgrade schema: remove usage limits from promo codes."""
    op.drop_column("promocode", "uses_count")
    op.drop_column("promocode", "max_uses")
