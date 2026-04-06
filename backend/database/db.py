from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from ..config import DATABASE_URL

# use check_same_thread flag for SQLite multithreading
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def init_db():
    """Create all tables in the database."""
    from . import models  # ensure models are imported

    Base.metadata.create_all(bind=engine)
