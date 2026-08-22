"""Create bounded agent investigation records.

Revision ID: 20260821_004
Revises: 20260821_003
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_004"
down_revision: str | None = "20260821_003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transaction_id", sa.String(length=36), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("recommendation", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("summary", sa.String(length=2_000), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("transaction_id", "assessment_id", "status", "recommendation"):
        op.create_index(f"ix_investigations_{column}", "investigations", [column], unique=False)


def downgrade() -> None:
    op.drop_table("investigations")
