from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: str
    risk_score: int = Field(ge=0, le=100)
    decision: str
    ml_probability: float = Field(ge=0, le=1)
    rules_score: float = Field(ge=0, le=100)
    anomaly_score: float = Field(ge=0, le=100)
    model_version: str
    reasons: list[str]
    feature_values: dict[str, Any]
    created_at: datetime


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    algorithm: str
    feature_names: list[str]
    parameters: dict[str, Any]
    metrics: dict[str, Any] | None
    trained_at: datetime


class ModelTrainingRequest(BaseModel):
    sample_count: int = Field(default=1_000, ge=200, le=10_000)
    seed: int = Field(default=42, ge=0)
