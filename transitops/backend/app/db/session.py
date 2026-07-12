"""SQLAlchemy engine and session factory.

Uses synchronous psycopg2 driver (deliberate choice: zero event-loop
pitfalls under the 8-hour hackathon clock; FastAPI runs sync endpoints
in a threadpool — documented tradeoff in docs/01-ARCHITECTURE.md §2).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # stale connection detection
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
