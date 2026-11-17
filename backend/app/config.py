"""
运行时配置：默认连接本机 Ollama，可通过环境变量切换地址和模型。

启动时加载 backend/.env，避免仅写在文件里却未 export 导致读不到。
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# app/config.py -> app/ -> backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    ollama_model: str
    ollama_keep_alive: str
    cors_allowed_origins: tuple[str, ...]
    frontend_dist_dir: str


def _csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = _env(name)
    if not value:
        return default
    items = tuple(item.strip().rstrip("/") for item in value.split(",") if item.strip())
    return items or default


def load_settings() -> Settings:
    return Settings(
        ollama_base_url=_env("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        or "http://127.0.0.1:11434",
        ollama_model=_env("OLLAMA_MODEL", "qwen3.5:9b") or "qwen3.5:9b",
        ollama_keep_alive=_env("OLLAMA_KEEP_ALIVE", "15m") or "15m",
        cors_allowed_origins=_csv_env(
            "CORS_ALLOWED_ORIGINS",
            (
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            ),
        ),
        frontend_dist_dir=_env("FRONTEND_DIST_DIR", "../frontend/dist") or "../frontend/dist",
    )
