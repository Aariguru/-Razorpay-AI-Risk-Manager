from datetime import datetime

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_transactions: int
    assessed_transactions: int
    assessment_coverage_percent: float = Field(ge=0, le=100)
    average_risk_score: float = Field(ge=0, le=100)
    allow_count: int
    manual_review_count: int
    block_count: int
    review_queue_count: int
    analyst_override_count: int


class RiskDistributionBucket(BaseModel):
    label: str
    minimum: int
    maximum: int
    count: int


class RiskDistribution(BaseModel):
    buckets: list[RiskDistributionBucket]


class RecentAssessment(BaseModel):
    transaction_id: str
    customer_id: str
    amount_paise: int
    occurred_at: datetime
    risk_score: int
    decision: str
    model_version: str
    reasons: list[str]


class RecentAssessmentList(BaseModel):
    items: list[RecentAssessment]
