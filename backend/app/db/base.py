from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Railway Postgres provides postgresql:// but we need postgresql+psycopg:// for psycopg3
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://") or _db_url.startswith("postgres://"):
    _db_url = "postgresql+psycopg://" + _db_url.split("://", 1)[1]

engine = create_engine(_db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
