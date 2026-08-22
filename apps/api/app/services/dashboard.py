"""Read-model queries for the future analyst dashboard."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ReviewDecision, RiskAssessment, Transaction
from app.schemas.dashboard import (
    DashboardSummary,
    RecentAssessment,
    RecentAssessmentList,
    RiskDistribution,
    RiskDistributionBucket,
)


def _latest_assessments(session: Session) -> list[RiskAssessment]:
    assessments = list(
        session.scalars(
            select(RiskAssessment).order_by(RiskAssessment.created_at.desc())
        )
    )
    latest_by_transaction: dict[str, RiskAssessment] = {}
    for assessment in assessments:
        latest_by_transaction.setdefault(assessment.transaction_id, assessment)
    return list(latest_by_transaction.values())


def get_summary(session: Session) -> DashboardSummary:
    transactions = list(session.scalars(select(Transaction)))
    assessments = _latest_assessments(session)
    reviewed_transaction_ids = set(session.scalars(select(ReviewDecision.transaction_id)))
    decisions = {"allow": 0, "manual_review": 0, "block": 0}
    for assessment in assessments:
        decisions[assessment.decision] = decisions.get(assessment.decision, 0) + 1
    queue_count = sum(
        1
        for assessment in assessments
        if assessment.decision == "manual_review"
        and assessment.transaction_id not in reviewed_transaction_ids
    )
    overrides = 0

    for review in session.scalars(select(ReviewDecision)):
        if review.assessment_id is None:
            continue

        matching_assessment = next(
            (item for item in assessments if item.id == review.assessment_id),
            None,
        )

        if matching_assessment is not None and review.decision != matching_assessment.decision:
            overrides += 1
    
    average = (
        round(sum(item.risk_score for item in assessments) / len(assessments), 2)
        if assessments
        else 0.0
    )
    return DashboardSummary(
        total_transactions=len(transactions),
        assessed_transactions=len(assessments),
        assessment_coverage_percent=(
            round(100 * len(assessments) / len(transactions), 2) if transactions else 0
        ),
        average_risk_score=average,
        allow_count=decisions["allow"],
        manual_review_count=decisions["manual_review"],
        block_count=decisions["block"],
        review_queue_count=queue_count,
        analyst_override_count=overrides,
    )


def get_risk_distribution(session: Session) -> RiskDistribution:
    assessments = _latest_assessments(session)
    definitions = (
        ("Low (0–34)", 0, 34),
        ("Review (35–69)", 35, 69),
        ("High (70–100)", 70, 100),
    )

    return RiskDistribution(
        buckets=[
            RiskDistributionBucket(
                label=label,
                minimum=minimum,
                maximum=maximum,
                count=sum(
                    1
                    for item in assessments
                    if minimum <= item.risk_score <= maximum
                ),
            )
            for label, minimum, maximum in definitions
        ]
    )


def get_recent_assessments(session: Session, limit: int) -> RecentAssessmentList:
    assessments = sorted(
        _latest_assessments(session), key=lambda item: item.created_at, reverse=True
    )[:limit]
    transaction_ids = [a.transaction_id for a in assessments]
    transactions = {
        item.id: item
        for item in session.scalars(
            select(Transaction).where(Transaction.id.in_(transaction_ids))
        )
    }
    return RecentAssessmentList(
        items=[
            RecentAssessment(
                transaction_id=assessment.transaction_id,
                customer_id=transactions[assessment.transaction_id].customer_id,
                amount_paise=transactions[assessment.transaction_id].amount_paise,
                occurred_at=transactions[assessment.transaction_id].occurred_at,
                risk_score=assessment.risk_score,
                decision=assessment.decision,
                model_version=assessment.model_version,
                reasons=assessment.reasons,
            )
            for assessment in assessments
            if assessment.transaction_id in transactions
        ]
    )
