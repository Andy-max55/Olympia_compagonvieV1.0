"""Couche d'accès à la base de données SQLite locale.

Fournit le moteur SQLAlchemy, la fabrique de sessions et la classe de
base déclarative. Aucune donnée métier n'est créée ici : ce module
ne gère que le cycle de vie de la connexion.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeMeta, Session, declarative_base, sessionmaker

_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_DATABASE_FILE: Path = _BACKEND_ROOT / "compagnon.db"
_DATABASE_URL: str = f"sqlite:///{_DATABASE_FILE.as_posix()}"

# check_same_thread=False : SQLite n'autorise qu'un thread par connexion
# par défaut. FastAPI exécute les dépendances dans un pool de threads.
engine: Engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    pool_pre_ping=True,
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base: DeclarativeMeta = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Fournit une session SQLAlchemy à une route FastAPI.

    La session est ouverte à l'entrée de la requête et toujours
    fermée dans ``finally``, y compris en cas d'exception.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
