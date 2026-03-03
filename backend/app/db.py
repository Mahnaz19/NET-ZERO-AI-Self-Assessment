from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings


engine = create_engine(settings.DATABASE_URL, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base = declarative_base()


def get_db() -> Session:
    """
    FastAPI dependency that provides a database session and ensures it is closed.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

