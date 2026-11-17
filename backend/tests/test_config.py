from app.config import load_settings


def test_default_cors_origins_are_local_dev(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    settings = load_settings()

    assert settings.cors_allowed_origins == (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )


def test_cors_origins_can_be_configured(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        " http://127.0.0.1:5173/ , https://app.example.com ",
    )

    settings = load_settings()

    assert settings.cors_allowed_origins == (
        "http://127.0.0.1:5173",
        "https://app.example.com",
    )
