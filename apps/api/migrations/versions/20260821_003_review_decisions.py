"""Create human review and feedback storage.

Revision ID: 20260821_003
Revises: 20260821_002
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_003"
down_revision: str | None = "20260821_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transaction_id", sa.String(length=36), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), nullable=True),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("outcome_label", sa.String(length=40), nullable=True),
        sa.Column("analyst_id", sa.String(length=100), nullable=False),
        sa.Column("notes", sa.String(length=1_000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("transaction_id", "assessment_id", "decision", "outcome_label"):
        op.create_index(f"ix_review_decisions_{column}", "review_decisions", [column], unique=False)


def downgrade() -> None:
    op.drop_table("review_decisions")
