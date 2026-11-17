"""
FastAPI 依赖别名：统一 Annotated 注入，满足静态检查与 OpenAPI 生成。
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db

DbSession = Annotated[Session, Depends(get_db)]
