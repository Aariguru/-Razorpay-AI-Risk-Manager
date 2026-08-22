from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Provider = Literal["mock", "openai"]
Recommendation = Literal["allow", "manual_review", "block"]


class InvestigationCreate(BaseModel):
    provider: Provider | None = None


class AgentRecommendation(BaseModel):
    recommendation: Recommendation
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=2_000)
    limitations: list[str] = Field(min_length=1, max_length=5)


class InvestigationRead(AgentRecommendation):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: str
    assessment_id: str | None
    status: str
    provider: str
    evidence: dict[str, Any]
    created_at: datetime