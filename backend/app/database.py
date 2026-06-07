from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs = {
        "connect_args": connect_args,
        "pool_pre_ping": True,
        "echo": settings.API_DEBUG,
    }
else:
    engine_kwargs = {
        "pool_pre_ping": True,
        "echo": settings.API_DEBUG,
        "pool_size": 10,
        "max_overflow": 20,
    }

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Provides a database session for requests, closing it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
