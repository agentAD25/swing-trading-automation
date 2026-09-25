"""Add durable canonical order-intent identity.

Revision ID: 0002_canonical_order_intents
Revises: 0001_offline_foundation
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_canonical_order_intents"
down_revision = "0001_offline_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "order_intents",
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("intent_id", sa.String(), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("canonical_intent", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("idempotency_key"),
        sa.UniqueConstraint("intent_id"),
    )


def downgrade() -> None:
    op.drop_table("order_intents")
