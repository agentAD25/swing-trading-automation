"""Create the minimal offline ledger and idempotency tables."""

import sqlalchemy as sa
from alembic import op

revision = "0001_offline_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("aggregate_type", sa.String(), nullable=False),
        sa.Column("aggregate_id", sa.String(), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("canonical_event", sa.JSON(), nullable=False),
        sa.UniqueConstraint("aggregate_type", "aggregate_id", "aggregate_version"),
    )
    op.create_table(
        "idempotency_records",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("canonical_result", sa.JSON(), nullable=False),
    )
    op.create_table(
        "outbox_items",
        sa.Column("intent_id", sa.String(), primary_key=True),
        sa.Column("idempotency_key", sa.String(), nullable=False, unique=True),
        sa.Column("state", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("outbox_items")
    op.drop_table("idempotency_records")
    op.drop_table("domain_events")
