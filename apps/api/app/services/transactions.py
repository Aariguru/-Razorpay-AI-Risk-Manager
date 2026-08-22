from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.schemas.transactions import TransactionCreate


def create_transaction(session: Session, payload: TransactionCreate) -> Transaction:
    transaction = Transaction(id=str(uuid4()), **payload.model_dump())
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def get_transaction(session: Session, transaction_id: str) -> Transaction | None:
    return session.get(Transaction, transaction_id)


def list_transactions(
    session: Session, *, limit: int, offset: int, customer_id: str | None, status: str | None
) -> tuple[list[Transaction], int]:
    statement = select(Transaction).order_by(Transaction.occurred_at.desc())
    count_statement = select(func.count()).select_from(Transaction)
    if customer_id:
        statement = statement.where(Transaction.customer_id == customer_id)
        count_statement = count_statement.where(Transaction.customer_id == customer_id)
    if status:
        statement = statement.where(Transaction.status == status)
        count_statement = count_statement.where(Transaction.status == status)
    items = list(session.scalars(statement.limit(limit).offset(offset)))
    total = session.scalar(count_statement) or 0
    return items, total
