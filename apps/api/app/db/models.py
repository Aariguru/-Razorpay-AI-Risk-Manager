from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Transaction(Base):
    """A tokenized payment event. Raw card data is intentionally never stored."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    external_reference: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(100), index=True)
    payment_token: Mapped[str] = mapped_column(String(128), index=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    payment_method: Mapped[str] = mapped_column(String(30), index=True)
    merchant_category: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    device_id: Mapped[str | None] = mapped_column(String(128), index=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    country_code: Mapped[str] = mapped_column(String(2), default="IN")
    city: Mapped[str | None] = mapped_column(String(80))
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelVersion(Base):
    """Auditable parameters and training metadata for a risk model."""

    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    version: Mapped[str] = mapped_column(String(40), unique=True)
    algorithm: Mapped[str] = mapped_column(String(80))
    feature_names: Mapped[list[str]] = mapped_column(JSON)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskAssessment(Base):
    """Stored, explainable output of the hybrid risk engine."""

    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(36), index=True)
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    decision: Mapped[str] = mapped_column(String(30), index=True)
    ml_probability: Mapped[float] = mapped_column()
    rules_score: Mapped[float] = mapped_column()
    anomaly_score: Mapped[float] = mapped_column()
    model_version: Mapped[str] = mapped_column(String(40))
    reasons: Mapped[list[str]] = mapped_column(JSON)
    feature_values: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewDecision(Base):
    """Human analyst decision and feedback for a risk-assessed transaction."""

    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(36), index=True)
    assessment_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String(30), index=True)
    outcome_label: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    analyst_id: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(String(1_000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Investigation(Base):
    """Evidence-bounded agent investigation; never a direct payment action."""

    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(36), index=True)
    assessment_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    provider: Mapped[str] = mapped_column(String(30))
    recommendation: Mapped[str] = mapped_column(String(30), index=True)
    confidence: Mapped[float] = mapped_column()
    summary: Mapped[str] = mapped_column(String(2_000))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON)
    limitations: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
