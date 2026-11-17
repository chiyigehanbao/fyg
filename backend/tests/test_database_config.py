from app.database import _engine_options
from scripts.database_smoke import mask_database_url


def test_sqlite_uses_thread_check_override() -> None:
    assert _engine_options("sqlite:///./data/app.db") == {
        "connect_args": {"check_same_thread": False},
    }


def test_postgresql_uses_pool_health_checks() -> None:
    assert _engine_options("postgresql+psycopg://postgres:postgres@127.0.0.1:5432/app") == {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }


def test_database_smoke_masks_password() -> None:
    assert (
        mask_database_url("postgresql+psycopg://postgres:secret@127.0.0.1:5432/app")
        == "postgresql+psycopg://postgres:***@127.0.0.1:5432/app"
    )
