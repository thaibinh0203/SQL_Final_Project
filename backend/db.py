"""Database engine and session management helpers."""

from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base so models stay in one metadata registry."""


@lru_cache(maxsize=1)
def get_engine():
    """Create one engine per process to keep connection pooling predictable."""

    settings = get_settings()
    return create_engine(
        settings.sqlalchemy_database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Build one session factory because sessions are created per request/workflow."""

    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a session with automatic commit or rollback for safe database access."""

    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
