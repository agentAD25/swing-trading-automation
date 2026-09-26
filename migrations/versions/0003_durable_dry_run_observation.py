"""Persist the authoritative DRY_RUN observation.

Revision ID: 0003_durable_dry_run_observation
Revises: 0002_canonical_order_intents
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_durable_dry_run_observation"
down_revision = "0002_canonical_order_intents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "order_intents",
        sa.Column("canonical_observation", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("order_intents", "canonical_observation")
