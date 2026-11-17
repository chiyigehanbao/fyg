import os
import tempfile
from pathlib import Path

_TEMP_DIR = tempfile.TemporaryDirectory()
_DB_PATH = Path(_TEMP_DIR.name) / "diagnosis-test-suite.db"

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"
os.environ["OLLAMA_MODEL"] = "test-model"


def pytest_sessionfinish() -> None:
    _TEMP_DIR.cleanup()
