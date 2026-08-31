"""
Database connection setup.

DEV: uses a local SQLite file (disasterlens.db) - zero setup required.
PROD: swap DATABASE_URL to a real Postgres URL, e.g.:
    postgresql://user:password@localhost:5432/disasterlens
Everything else (models, queries) stays exactly the same thanks to SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./disasterlens.db"

# check_same_thread is only needed for SQLite; harmless to leave for now,
# but remove it if/when you switch to Postgres.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency - gives each request its own DB session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
