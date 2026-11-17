"""数据库引擎与会话工厂。"""

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(_DATA_DIR.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{_DATA_DIR / 'app.db'}"


def _engine_options(database_url: str) -> dict[str, object]:
    """Return SQLAlchemy options that match the configured database driver."""
    scheme = urlparse(database_url).scheme
    if scheme.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }


engine = create_engine(DATABASE_URL, **_engine_options(DATABASE_URL))


class Base(DeclarativeBase):
    """ORM 模型基类。"""


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    为每个请求提供独立会话，用完关闭。

    Yields:
        Session: SQLAlchemy 会话实例。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
