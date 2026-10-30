"""
Food Verse AI — Database Layer (Part 4)
SQLAlchemy engine + session factory.
DATABASE_URL defaults to SQLite (local dev).
Set DATABASE_URL=postgresql+psycopg2://user:pass@host/db for production.
"""
from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import PROJECT_ROOT

# ── URL resolution ────────────────────────────────────────────────────────────
_db_url = os.environ.get("DATABASE_URL", "")
if not _db_url:
    _sqlite_path = PROJECT_ROOT / "food_verse.db"
    _db_url = f"sqlite:///{_sqlite_path}"

# SQLite needs check_same_thread=False; ignored by other drivers
_connect_args: dict = {}
if _db_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    _db_url,
    connect_args=_connect_args,
    echo=False,          # set True only for SQL debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Declarative base shared by all ORM models ────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db():
    """Yield a database session, closing it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Table creation helper (used on startup) ───────────────────────────────────
def create_all_tables() -> None:
    """Create all tables that do not yet exist (non-destructive)."""
    # Import models so SQLAlchemy registers them before create_all
    import backend.models.db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
