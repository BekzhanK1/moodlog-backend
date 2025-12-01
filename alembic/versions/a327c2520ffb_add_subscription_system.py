"""
Add subscription system: user subscription fields, subscription and payment tables

Revision ID: a327c2520ffb
Revises: 9434d4d97626
Create Date: 2025-12-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = 'a327c2520ffb'
down_revision: Union[str, Sequence[str], None] = '9434d4d97626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add subscription system tables and user fields."""

    # Add subscription fields to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('plan', sa.String(),
                            nullable=False, server_default='free'))
        batch_op.add_column(sa.Column('plan_started_at',
                            sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('plan_expires_at',
                            sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('trial_used', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column(
            'subscription_status', sa.String(), nullable=False, server_default='active'))
        batch_op.create_index('ix_user_plan', ['plan'])
        batch_op.create_index('ix_user_subscription_status', [
                              'subscription_status'])

    # Create subscription table
    op.create_table(
        'subscription',
        sa.Column('id', sa.Uuid(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey(
            'user.id'), nullable=False, index=True),
        sa.Column('plan', sa.String(), nullable=False, index=True),
        sa.Column('status', sa.String(), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
    )

    # Create payment table
    op.create_table(
        'payment',
        sa.Column('id', sa.Uuid(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey(
            'user.id'), nullable=False, index=True),
        sa.Column('subscription_id', sa.Uuid(), sa.ForeignKey(
            'subscription.id'), nullable=True, index=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(),
                  nullable=False, server_default='KZT'),
        sa.Column('plan', sa.String(), nullable=False, index=True),
        sa.Column('webkassa_order_id', sa.String(),
                  nullable=True, unique=True, index=True),
        sa.Column('webkassa_receipt_id', sa.String(),
                  nullable=True, index=True),
        sa.Column('webkassa_status', sa.String(), nullable=True, index=True),
        sa.Column('status', sa.String(), nullable=False, index=True),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('payment_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema: remove subscription system tables and user fields."""

    # Drop payment table
    op.drop_table('payment')

    # Drop subscription table
    op.drop_table('subscription')

    # Remove subscription fields from user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index('ix_user_subscription_status')
        batch_op.drop_index('ix_user_plan')
        batch_op.drop_column('subscription_status')
        batch_op.drop_column('trial_used')
        batch_op.drop_column('plan_expires_at')
        batch_op.drop_column('plan_started_at')
        batch_op.drop_column('plan')
