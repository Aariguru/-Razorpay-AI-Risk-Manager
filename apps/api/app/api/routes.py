from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.investigation import get_latest_investigation, investigate_transaction
from app.core.config import get_settings
from app.db.database import get_db_session
from app.schemas.dashboard import DashboardSummary, RecentAssessmentList, RiskDistribution
from app.schemas.investigations import InvestigationCreate, InvestigationRead
from app.schemas.reviews import ReviewDecisionCreate, ReviewDecisionRead
from app.schemas.risk import ModelTrainingRequest, ModelVersionRead, RiskAssessmentRead
from app.schemas.transactions import TransactionCreate, TransactionList, TransactionRead
from app.services.dashboard import get_recent_assessments, get_risk_distribution, get_summary
from app.services.reviews import create_review_decision, get_latest_review
from app.services.risk import assess_transaction, get_latest_assessment, train_synthetic_baseline
from app.services.transactions import create_transaction, get_transaction, list_transactions

router = APIRouter(prefix="/api/v1", tags=["platform"])


class PlatformInfo(BaseModel):
    name: str
    version: str
    environment: str
    phase: str


@router.get("/platform", response_model=PlatformInfo, summary="Get platform metadata")
def get_platform_info() -> PlatformInfo:
    settings = get_settings()
    return PlatformInfo(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        phase="data-foundation",
    )


@router.post(
    "/transactions",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["transactions"],
    summary="Ingest a tokenized transaction",
)
def ingest_transaction(
    payload: TransactionCreate, session: Session = Depends(get_db_session)
) -> TransactionRead:
    transaction = create_transaction(session, payload)
    return TransactionRead.model_validate(transaction)


@router.get(
    "/transactions",
    response_model=TransactionList,
    tags=["transactions"],
    summary="List ingested transactions",
)
def get_transactions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    customer_id: str | None = Query(default=None, max_length=100),
    status_filter: str | None = Query(default=None, alias="status", max_length=30),
    session: Session = Depends(get_db_session),
) -> TransactionList:
    items, total = list_transactions(
        session, limit=limit, offset=offset, customer_id=customer_id, status=status_filter
    )
    return TransactionList(
    items=[TransactionRead.model_validate(item) for item in items],
    limit=limit,
    offset=offset,
    total=total,
)

@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionRead,
    tags=["transactions"],
    summary="Get one ingested transaction",
)
def get_transaction_by_id(
    transaction_id: str, session: Session = Depends(get_db_session)
) -> TransactionRead:
    transaction = get_transaction(session, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)


@router.post(
    "/transactions/{transaction_id}/assessments",
    response_model=RiskAssessmentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["risk"],
    summary="Calculate an explainable hybrid risk score",
)
def create_risk_assessment(
    transaction_id: str, session: Session = Depends(get_db_session)
) -> RiskAssessmentRead:
    transaction = get_transaction(session, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    assessment = assess_transaction(session, transaction)
    return RiskAssessmentRead.model_validate(assessment)


@router.get(
    "/transactions/{transaction_id}/assessments/latest",
    response_model=RiskAssessmentRead,
    tags=["risk"],
    summary="Get the latest risk assessment for a transaction",
)
def get_latest_risk_assessment(
    transaction_id: str, session: Session = Depends(get_db_session)
) -> RiskAssessmentRead:
    assessment = get_latest_assessment(session, transaction_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk assessment not found",
        )
    return RiskAssessmentRead.model_validate(assessment)


@router.post(
    "/models/train",
    response_model=ModelVersionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["models"],
    summary="Train a reproducible logistic baseline using synthetic labels",
)
def train_model(
    payload: ModelTrainingRequest, session: Session = Depends(get_db_session)
) -> ModelVersionRead:
    model_version = train_synthetic_baseline(
        session,
        payload.sample_count,
        payload.seed,
    )
    return ModelVersionRead.model_validate(model_version)


@router.post(
    "/transactions/{transaction_id}/reviews",
    response_model=ReviewDecisionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["reviews"],
    summary="Record an analyst decision and feedback label",
)
def submit_review(
    transaction_id: str,
    payload: ReviewDecisionCreate,
    session: Session = Depends(get_db_session),
) -> ReviewDecisionRead:
    transaction = get_transaction(session, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    assessment = get_latest_assessment(session, transaction_id)
    review = create_review_decision(
        session,
        transaction_id=transaction_id,
        assessment_id=assessment.id if assessment else None,
        payload=payload,
    )

    return ReviewDecisionRead.model_validate(review)


@router.get(
    "/transactions/{transaction_id}/reviews/latest",
    response_model=ReviewDecisionRead,
    tags=["reviews"],
    summary="Get the latest analyst review for a transaction",
)
def get_latest_transaction_review(
    transaction_id: str, session: Session = Depends(get_db_session)
) -> ReviewDecisionRead:
    review = get_latest_review(session, transaction_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review decision not found",
        )
    return ReviewDecisionRead.model_validate(review)


@router.get("/dashboard/summary", response_model=DashboardSummary, tags=["dashboard"])
def dashboard_summary(session: Session = Depends(get_db_session)) -> DashboardSummary:
    return get_summary(session)


@router.get("/dashboard/risk-distribution", response_model=RiskDistribution, tags=["dashboard"])
def dashboard_risk_distribution(session: Session = Depends(get_db_session)) -> RiskDistribution:
    return get_risk_distribution(session)


@router.get(
    "/dashboard/recent-assessments",
    response_model=RecentAssessmentList,
    tags=["dashboard"],
)
def dashboard_recent_assessments(
    limit: int = Query(default=10, ge=1, le=50), session: Session = Depends(get_db_session)
) -> RecentAssessmentList:
    return get_recent_assessments(session, limit)


@router.post(
    "/transactions/{transaction_id}/investigations",
    response_model=InvestigationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["investigations"],
    summary="Run a bounded AI risk investigation",
)
def create_investigation(
    transaction_id: str,
    payload: InvestigationCreate,
    session: Session = Depends(get_db_session),
) -> InvestigationRead:
    transaction = get_transaction(session, transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    try:
        investigation = investigate_transaction(
            session,
            transaction,
            payload.provider,
        )

        return InvestigationRead.model_validate(investigation)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/transactions/{transaction_id}/investigations/latest",
    response_model=InvestigationRead,
    tags=["investigations"],
    summary="Get the latest AI investigation",
)
def get_latest_transaction_investigation(
    transaction_id: str, session: Session = Depends(get_db_session)
) -> InvestigationRead:
    investigation = get_latest_investigation(session, transaction_id)
    if investigation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")
    return InvestigationRead.model_validate(investigation)
