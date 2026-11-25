"""Connexion à la base de données (PostgreSQL en production, SQLite en local et en test)."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# SQLite a besoin de cette option pour être utilisé par plusieurs threads (serveur web)
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """Ouvre une session par requête et la ferme toujours à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
