"""Agentic investigation workflow with whitelisted, read-only evidence tools."""

import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Investigation, RiskAssessment, Transaction
from app.schemas.investigations import AgentRecommendation, Recommendation
from app.services.risk import get_latest_assessment


class RecommendationProvider(Protocol):
    name: str

    def recommend(self, evidence: dict[str, Any]) -> AgentRecommendation: ...


class MockRecommendationProvider:
    """Deterministic local provider for tests, demos, and keyless development."""

    name = "mock"

    def recommend(self, evidence: dict[str, Any]) -> AgentRecommendation:
        assessment = evidence["risk_assessment"]
        score = assessment["risk_score"]
        recommendation: Recommendation
        if score >= 70:
            recommendation = "block"
            confidence = 0.82
        elif score >= 35:
            recommendation = "manual_review"
            confidence = 0.72
        else:
            recommendation = "allow"
            confidence = 0.7
        signals = "; ".join(assessment["reasons"][:2])
        return AgentRecommendation(
            recommendation=recommendation,
            confidence=confidence,
            summary=(
                f"The stored hybrid score is {score}/100. Evidence reviewed: {signals} "
                f"Recommended action: {recommendation.replace('_', ' ')}."
            ),
            limitations=[
                "This assessment uses synthetic or locally stored data only.",
                "No external identity, chargeback, payment-network, or private "
                "Razorpay data was checked.",
                "A human analyst must make the final simulated review decision.",
            ],
        )


class OpenAIRecommendationProvider:
    """Optional OpenAI Responses API provider with strict JSON-schema output."""

    name = "openai"

    def recommend(self, evidence: dict[str, Any]) -> AgentRecommendation:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required when provider is openai")
        from openai import OpenAI

        settings = get_settings()
        client = OpenAI()
        response = client.responses.create(
            model=settings.openai_model,
            store=False,
            max_output_tokens=500,
            instructions=(
                "You are a payment-risk investigation assistant. Use only the supplied evidence. "
                "Never claim access to Razorpay systems, external sources, or facts absent "
                "from evidence. Recommend allow, manual_review, or block as decision support "
                "only; never execute an action. Clearly name uncertainty in limitations."
            ),
            input=json.dumps(evidence),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "investigation_recommendation",
                    "strict": True,
                    "schema": AgentRecommendation.model_json_schema(),
                }
            },
        )
        return AgentRecommendation.model_validate_json(response.output_text)


def _normalise_timestamp(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _customer_history_tool(session: Session, transaction: Transaction) -> dict[str, Any]:
    history = list(
        session.scalars(
            select(Transaction).where(
                Transaction.customer_id == transaction.customer_id,
                Transaction.id != transaction.id,
            )
        )
    )
    return {
        "prior_transaction_count": len(history),
        "prior_captured_count": sum(item.status == "captured" for item in history),
        "prior_failed_count": sum(item.status == "failed" for item in history),
        "known_country_codes": sorted({item.country_code for item in history}),
        "known_device_count": len({item.device_id for item in history if item.device_id}),
    }


def _device_context_tool(session: Session, transaction: Transaction) -> dict[str, Any]:
    if not transaction.device_id:
        return {"device_present": False, "device_transaction_count": 0}
    transactions = list(
        session.scalars(select(Transaction).where(Transaction.device_id == transaction.device_id))
    )
    window_start = _normalise_timestamp(transaction.occurred_at) - timedelta(hours=24)
    return {
        "device_present": True,
        "device_transaction_count": len(transactions),
        "device_customer_count": len({item.customer_id for item in transactions}),
        "device_transactions_24h": sum(
            _normalise_timestamp(item.occurred_at) >= window_start for item in transactions
        ),
    }


def _policy_tool() -> dict[str, Any]:
    return {
        "score_thresholds": {"allow": "0-34", "manual_review": "35-69", "block": "70-100"},
        "agent_boundary": "Recommendation only; no autonomous payment action.",
    }


def collect_evidence(
    session: Session,
    transaction: Transaction,
    assessment: RiskAssessment,
) -> dict[str, Any]:
    """Invoke the complete fixed allowlist of read-only investigation tools."""
    return {
        "transaction": {
            "id": transaction.id,
            "customer_id": transaction.customer_id,
            "amount_paise": transaction.amount_paise,
            "currency": transaction.currency,
            "payment_method": transaction.payment_method,
            "merchant_category": transaction.merchant_category,
            "status": transaction.status,
            "country_code": transaction.country_code,
            "city": transaction.city,
        },
        "risk_assessment": {
            "risk_score": assessment.risk_score,
            "decision": assessment.decision,
            "ml_probability": assessment.ml_probability,
            "rules_score": assessment.rules_score,
            "anomaly_score": assessment.anomaly_score,
            "model_version": assessment.model_version,
            "reasons": assessment.reasons,
            "feature_values": assessment.feature_values,
        },
        "customer_history": _customer_history_tool(session, transaction),
        "device_context": _device_context_tool(session, transaction),
        "policy": _policy_tool(),
    }


def _provider(name: str) -> RecommendationProvider:
    if name == "openai":
        return OpenAIRecommendationProvider()
    return MockRecommendationProvider()


def investigate_transaction(
    session: Session, transaction: Transaction, requested_provider: str | None
) -> Investigation:
    assessment = get_latest_assessment(session, transaction.id)
    if assessment is None:
        raise ValueError("A risk assessment is required before investigation")
    configured_provider = get_settings().agent_provider
    provider = _provider(requested_provider or configured_provider)
    evidence = collect_evidence(session, transaction, assessment)
    recommendation = provider.recommend(evidence)
    investigation = Investigation(
        id=str(uuid4()),
        transaction_id=transaction.id,
        assessment_id=assessment.id,
        status="completed",
        provider=provider.name,
        recommendation=recommendation.recommendation,
        confidence=recommendation.confidence,
        summary=recommendation.summary,
        evidence=evidence,
        limitations=recommendation.limitations,
    )
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    return investigation


def get_latest_investigation(session: Session, transaction_id: str) -> Investigation | None:
    return session.scalar(
        select(Investigation)
        .where(Investigation.transaction_id == transaction_id)
        .order_by(Investigation.created_at.desc())
    )
