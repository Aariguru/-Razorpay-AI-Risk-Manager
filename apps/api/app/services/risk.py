"""Explainable hybrid scoring with a small, reproducible logistic-regression baseline."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import exp, log1p
from random import Random
from statistics import median
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelVersion, RiskAssessment, Transaction

FEATURE_NAMES = (
    "amount_log_scaled",
    "velocity_10m",
    "failed_attempts_24h",
    "is_new_device",
    "is_unusual_country",
    "is_failed_payment",
)
DEFAULT_WEIGHTS = (-4.1, 1.55, 0.52, 0.46, 0.95, 0.85, 1.2)


@dataclass(frozen=True)
class ScoreComponents:
    ml_probability: float
    rules_score: float
    anomaly_score: float
    reasons: list[str]
    features: dict[str, float]


def _sigmoid(value: float) -> float:
    capped = max(-30.0, min(30.0, value))
    return 1.0 / (1.0 + exp(-capped))


def _normalise_timestamp(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _features(session: Session, transaction: Transaction) -> dict[str, float]:
    occurred_at = _normalise_timestamp(transaction.occurred_at)
    history = select(Transaction).where(
        Transaction.customer_id == transaction.customer_id,
        Transaction.id != transaction.id,
        Transaction.occurred_at <= occurred_at,
    )
    prior = list(session.scalars(history))
    prior_amounts = [item.amount_paise for item in prior if item.status == "captured"]
    baseline_amount = float(median(prior_amounts)) if prior_amounts else 49_900.0
    amount_ratio = transaction.amount_paise / max(baseline_amount, 1.0)
    velocity_start = occurred_at - timedelta(minutes=10)
    velocity = sum(
        1 for item in prior if _normalise_timestamp(item.occurred_at) >= velocity_start
    )
    failure_start = occurred_at - timedelta(hours=24)
    failures = sum(
        1
        for item in prior
        if item.status == "failed" and _normalise_timestamp(item.occurred_at) >= failure_start
    )
    is_new_device = float(
        bool(transaction.device_id)
        and not any(item.device_id == transaction.device_id for item in prior)
    )
    is_unusual_country = float(
        bool(prior)
        and not any(item.country_code == transaction.country_code for item in prior)
    )
    return {
        "amount_log_scaled": min(log1p(amount_ratio) / 2.3, 2.0),
        "velocity_10m": min(velocity / 5.0, 2.0),
        "failed_attempts_24h": min(failures / 3.0, 2.0),
        "is_new_device": is_new_device,
        "is_unusual_country": is_unusual_country,
        "is_failed_payment": float(transaction.status == "failed"),
        "amount_ratio": round(amount_ratio, 2),
        "customer_velocity_10m": float(velocity),
        "customer_failures_24h": float(failures),
    }


def _latest_model(session: Session) -> ModelVersion | None:
    return session.scalar(select(ModelVersion).order_by(ModelVersion.trained_at.desc()))


def _weights(model: ModelVersion | None) -> tuple[float, ...]:
    if model is None:
        return DEFAULT_WEIGHTS
    values = model.parameters.get("weights", [])
    if len(values) != len(FEATURE_NAMES) + 1:
        return DEFAULT_WEIGHTS
    return tuple(float(value) for value in values)


def _rule_score(features: dict[str, float]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if features["amount_ratio"] >= 4:
        score += 35
        reasons.append(
            f"Amount is {features['amount_ratio']:.1f}× the customer's captured-payment "
            "median."
        )
    if features["customer_velocity_10m"] >= 3:
        score += 30
        reasons.append(
            f"{int(features['customer_velocity_10m'])} prior attempts in the preceding "
            "10 minutes."
        )
    if features["customer_failures_24h"] >= 2:
        score += 20
        reasons.append(
            f"{int(features['customer_failures_24h'])} failed attempts in the preceding "
            "24 hours."
        )
    if features["is_new_device"]:
        score += 10
        reasons.append("Device has not appeared in this customer’s prior transaction history.")
    if features["is_unusual_country"]:
        score += 20
        reasons.append("Country differs from the customer’s recorded transaction history.")
    return min(score, 100.0), reasons


def calculate_components(session: Session, transaction: Transaction) -> ScoreComponents:
    features = _features(session, transaction)
    model = _latest_model(session)
    weights = _weights(model)
    linear_score = weights[0] + sum(
        weight * features[name] for weight, name in zip(weights[1:], FEATURE_NAMES, strict=True)
    )
    ml_probability = _sigmoid(linear_score)
    rules_score, reasons = _rule_score(features)
    anomaly_score = min(
        100.0,
        25 * max(0.0, features["amount_log_scaled"] - 0.3)
        + 20 * features["is_new_device"]
        + 25 * features["is_unusual_country"],
    )
    if not reasons:
        reasons.append("No high-severity behavioral rule was triggered.")
    reasons.insert(
        0,
        f"Logistic baseline estimates a {ml_probability:.0%} fraud-likelihood signal.",
    )
    return ScoreComponents(ml_probability, rules_score, anomaly_score, reasons, features)


def assess_transaction(session: Session, transaction: Transaction) -> RiskAssessment:
    components = calculate_components(session, transaction)
    model = _latest_model(session)
    risk_score = round(
        100
        * (
            0.65 * components.ml_probability
            + 0.25 * (components.rules_score / 100)
            + 0.10 * (components.anomaly_score / 100)
        )
    )
    decision = "block" if risk_score >= 70 else "manual_review" if risk_score >= 35 else "allow"
    assessment = RiskAssessment(
        id=str(uuid4()),
        transaction_id=transaction.id,
        risk_score=risk_score,
        decision=decision,
        ml_probability=components.ml_probability,
        rules_score=components.rules_score,
        anomaly_score=components.anomaly_score,
        model_version=model.version if model else "synthetic-logistic-default-v1",
        reasons=components.reasons,
        feature_values=components.features,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


def get_latest_assessment(session: Session, transaction_id: str) -> RiskAssessment | None:
    return session.scalar(
        select(RiskAssessment)
        .where(RiskAssessment.transaction_id == transaction_id)
        .order_by(RiskAssessment.created_at.desc())
    )


def train_synthetic_baseline(session: Session, sample_count: int, seed: int) -> ModelVersion:
    """Fit logistic-regression weights by gradient descent on labeled synthetic feature vectors."""
    random = Random(seed)
    samples: list[tuple[list[float], int]] = []
    for _ in range(sample_count):
        vector = [
            random.random() * 1.8,
            random.random() * 1.5,
            random.random() * 1.5,
            float(random.random() < 0.25),
            float(random.random() < 0.12),
            float(random.random() < 0.18),
        ]
        latent = -4.1 + sum(
            weight * value
            for weight, value in zip(DEFAULT_WEIGHTS[1:], vector, strict=True)
        )
        label = int(random.random() < _sigmoid(latent))
        samples.append((vector, label))
    weights = [0.0] * (len(FEATURE_NAMES) + 1)
    learning_rate = 0.15
    for _ in range(350):
        gradients = [0.0] * len(weights)
        for vector, label in samples:
            prediction = _sigmoid(
                weights[0]
                + sum(
                    w * x for w, x in zip(weights[1:], vector, strict=True)
                )
            )
            error = prediction - label
            gradients[0] += error
            for index, value in enumerate(vector, start=1):
                gradients[index] += error * value
        for index in range(len(weights)):
            weights[index] -= learning_rate * gradients[index] / len(samples)
    version = f"synthetic-logistic-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    model = ModelVersion(
        id=str(uuid4()),
        name="Synthetic logistic risk baseline",
        version=version,
        algorithm="logistic_regression_gradient_descent",
        feature_names=list(FEATURE_NAMES),
        parameters={"weights": weights, "learning_rate": learning_rate, "iterations": 350},
        metrics={"training_samples": sample_count, "label_source": "synthetic-risk-simulator"},
    )
    session.add(model)
    session.commit()
    session.refresh(model)
    return model
