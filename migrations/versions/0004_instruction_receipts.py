"""Add the instruction-receipt table.

Revision ID: 0004_instruction_receipts
Revises: 0003_durable_dry_run_observation

Writing this revision does not execute it. The Alembic target guard refuses
every revision whose identifier starts with 0004.
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_instruction_receipts"
down_revision = "0003_durable_dry_run_observation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instruction_receipts",
        sa.Column("receipt_key", sa.String(), nullable=False),
        sa.Column("content_digest", sa.String(64), nullable=False),
        sa.Column("disposition", sa.String(), nullable=False),
        sa.Column("message_type", sa.String(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("instruction_ids", sa.JSON(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=True),
        sa.Column("provider_type", sa.String(), nullable=False),
        sa.Column("parser_version", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column("retention_policy", sa.String(), nullable=False),
        sa.Column("provider_message_ref", sa.String(), nullable=True),
        sa.Column("source_timestamp", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("receipt_key"),
    )


def downgrade() -> None:
    op.drop_table("instruction_receipts")
