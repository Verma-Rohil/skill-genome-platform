"""
Skill Genome Platform — Database Connection
=============================================
SQLAlchemy engine and session management for MySQL.

WHY SQLAlchemy (not raw SQL):
- ORM gives us Python objects instead of dict rows — type-safe, IDE-friendly
- Migration support via Alembic (future extension)
- Connection pooling built-in (critical for production)
- Prevents SQL injection via parameterized queries

WHY NOT Django ORM:
- We're using FastAPI, not Django. Mixing frameworks adds unnecessary complexity.

PATTERN: Repository Pattern
- database.py handles CONNECTION (engine, session)
- models/ define SCHEMA (what tables look like)
- services/ contain BUSINESS LOGIC (queries, transformations)
- This separation means we can swap MySQL for PostgreSQL by changing ONE file
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

# --- Engine ---
# pool_pre_ping: Tests connection health before using it (handles MySQL timeouts)
# echo: Logs SQL statements when API_DEBUG is True (great for development)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.API_DEBUG,
    pool_size=10,
    max_overflow=20,
)

# --- Session Factory ---
# autocommit=False: We explicitly commit transactions (safer)
# autoflush=False: We control when changes are flushed to DB (predictable)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# --- Base Class ---
# All ORM models inherit from this
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.

    USAGE in a route:
        @router.get("/skills")
        def list_skills(db: Session = Depends(get_db)):
            ...

    WHY generator pattern:
    - Session is created per-request
    - Automatically closed after response (even on errors)
    - Prevents connection leaks
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
