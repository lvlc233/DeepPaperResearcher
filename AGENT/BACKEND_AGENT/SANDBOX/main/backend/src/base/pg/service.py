# TODO: 待测试
"""
开发者: BackendAgent
当前版本: pg_service_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:pg_service_v0_1:提供数据库引擎与会话管理、初始化建表能力，供 controller/service 层注入使用]
"""

from __future__ import annotations

import os
import threading
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine


_engine_lock = threading.Lock()
_engine = None


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    return "sqlite:///./dev.db"


def get_engine():
    global _engine
    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is not None:
            return _engine

        url = _database_url()
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        _engine = create_engine(url, echo=False, connect_args=connect_args)
        return _engine


def init_db() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    engine = get_engine()
    with Session(engine) as session:
        yield session
