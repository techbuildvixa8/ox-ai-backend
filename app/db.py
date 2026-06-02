"""SQLite database wiring (SQLAlchemy).

Provides the engine, a session factory, the declarative Base, a FastAPI
dependency (get_db), and init_db() to create tables on startup. Only the users
table exists at this phase.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

# check_same_thread=False is required for SQLite under the threaded dev server.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for all imported models. Safe to call repeatedly."""
    # Import models so they register on Base.metadata before create_all.
    from app.models import user as _user  # noqa: F401

    Base.metadata.create_all(bind=engine)
