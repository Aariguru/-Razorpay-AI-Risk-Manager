from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal["allow", "manual_review", "block"]
OutcomeLabel = Literal["confirmed_fraud", "false_positive", "legitimate", "insufficient_evidence"]


class ReviewDecisionCreate(BaseModel):
    decision: Decision
    outcome_label: OutcomeLabel | None = None
    analyst_id: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=1_000)


class ReviewDecisionRead(ReviewDecisionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: str
    assessment_id: str | None
    created_at: datetime
