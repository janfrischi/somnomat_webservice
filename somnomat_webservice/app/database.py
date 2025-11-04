from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
# Import settings
from app.config import settings
from typing import Generator

# Create the database engine
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
class Base(DeclarativeBase):
    pass

# FastAPI dependency
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

