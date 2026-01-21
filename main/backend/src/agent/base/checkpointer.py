"""
开发者: LangGraphAgent
当前版本: v1.1.0
创建时间: 2026-01-08 18:10
更新时间: 2026-01-14 17:00
更新记录: 
    [2026-01-08 18:10:v1.0.0:实现 Checkpointer 工厂方法,当前默认使用 MemorySaver]
    [2026-01-14 17:00:v1.1.0:集成 AsyncPostgresSaver, 支持持久化配置]
"""

from typing import Any, Optional
from langgraph.checkpoint.memory import MemorySaver
from contextlib import asynccontextmanager

# 尝试导入 PostgresSaver
# TODO: 这里感觉可以复用 src.base.pg下的内容,而不是单独写一个。而且我不太希望支持内容,而是要求pg,避免数据丢失,硬是要的话可以仅在测试环境用内存的。
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncConnectionPool
    HAS_POSTGRES_CHECKPOINT = True
except ImportError:
    HAS_POSTGRES_CHECKPOINT = False

try:
    from base.config import settings
except ImportError:
    # Fallback if src is not in path directly but via relative
    from base.config import settings

def get_memory_checkpointer() -> MemorySaver:
    """返回内存检查点保存器"""
    return MemorySaver()

@asynccontextmanager
async def get_postgres_checkpointer_context() -> Any:
    """
    获取 Postgres 检查点保存器的上下文管理器。
    使用 psycopg 连接池。
    """
    if not HAS_POSTGRES_CHECKPOINT:
        raise ImportError("langgraph-checkpoint-postgres or psycopg_pool not installed.")
        
    conn_string = settings.database_url
    # 确保使用 postgresql:// 协议 (SQLAlchemy 可能使用 postgresql+asyncpg://)
    if conn_string.startswith("postgresql+asyncpg://"):
        conn_string = conn_string.replace("postgresql+asyncpg://", "postgresql://")
    
    # 创建连接池
    async with AsyncConnectionPool(
        conninfo=conn_string,
        max_size=20,
        kwargs={"autocommit": True}
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        # 确保表已创建
        await checkpointer.setup()
        yield checkpointer

def get_checkpointer() -> Any:
    """
    获取默认的 Checkpointer。
    注意: 目前为了兼容模块级导入时的同步调用，默认返回 MemorySaver。
    生产环境建议在应用启动时使用 get_postgres_checkpointer_context 初始化图。
    """
    return get_memory_checkpointer()
