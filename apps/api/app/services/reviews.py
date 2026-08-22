from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ReviewDecision
from app.schemas.reviews import ReviewDecisionCreate


def create_review_decision(
    session: Session,
    *,
    transaction_id: str,
    assessment_id: str | None,
    payload: ReviewDecisionCreate,
) -> ReviewDecision:
    review = ReviewDecision(
        id=str(uuid4()),
        transaction_id=transaction_id,
        assessment_id=assessment_id,
        **payload.model_dump(),
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review


def get_latest_review(session: Session, transaction_id: str) -> ReviewDecision | None:
    return session.scalar(
        select(ReviewDecision)
        .where(ReviewDecision.transaction_id == transaction_id)
        .order_by(ReviewDecision.created_at.desc())
    )
