"""
Database configuration module.
Sets up SQLAlchemy engine, session factory, and Base class.
Provides a dependency-injectable get_db() generator for FastAPI routes.
Supports both MySQL and SQLite backends.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# ── SQLAlchemy Engine ─────────────────────────────────────────
connect_args = {}
if settings.DB_TYPE.lower() == "sqlite":
    # SQLite requires this for FastAPI's threaded concurrency
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.APP_DEBUG,
    connect_args=connect_args,
)

# Enable WAL mode and foreign keys for SQLite
if settings.DB_TYPE.lower() == "sqlite":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ── Session Factory ───────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative Base ──────────────────────────────────────────
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.
    Ensures the session is properly closed after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
