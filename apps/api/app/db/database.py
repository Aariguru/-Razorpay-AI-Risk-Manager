from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for persisted entities."""


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def initialise_database() -> None:
    """(Re)create development tables; production deployments should use Alembic migrations.

    This routine drops existing tables then recreates them to ensure a clean
    schema on each application startup (suitable for local development and
    tests where a fresh database is expected).
    """
    from app.db import models  # noqa: F401

    # Ensure a clean schema on startup to avoid leftover test data causing unique
    # constraint conflicts during repeated local runs.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
