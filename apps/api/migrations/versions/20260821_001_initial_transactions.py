"""Create the initial tokenized transaction store.

Revision ID: 20260821_001
Revises:
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("external_reference", sa.String(length=100), nullable=True),
        sa.Column("customer_id", sa.String(length=100), nullable=False),
        sa.Column("payment_token", sa.String(length=128), nullable=False),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column("merchant_category", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_reference"),
    )
    for column in ("customer_id", "payment_token", "payment_method", "status", "occurred_at", "device_id", "ip_hash"):
        op.create_index(f"ix_transactions_{column}", "transactions", [column], unique=False)


def downgrade() -> None:
    op.drop_table("transactions")
