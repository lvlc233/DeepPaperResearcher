'''
开发者: BackendAgent
当前版本: v1.0_redis_init
创建时间: 2026-01-14 14:30:00
更新时间: 2026-01-14 14:30:00
更新记录: 
    [2026-01-14 14:30:00:v1.0_redis_init:初始化Redis客户端连接]
'''

from typing import Optional, AsyncGenerator
import redis.asyncio as redis
from base.config import settings
from loguru import logger

class RedisService:
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_pool(cls) -> redis.ConnectionPool:
        if cls._pool is None:
            logger.info(f"Creating Redis connection pool: {settings.redis_url}")
            cls._pool = redis.ConnectionPool.from_url(
                settings.redis_url, 
                encoding="utf-8", 
                decode_responses=True
            )
        return cls._pool

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            pool = cls.get_pool()
            cls._client = redis.Redis(connection_pool=pool)
        return cls._client
    
    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.close()
            logger.info("Redis client closed")
        if cls._pool:
            await cls._pool.disconnect()
            logger.info("Redis connection pool disconnected")

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    FastAPI dependency for Redis client.
    """
    client = RedisService.get_client()
    try:
        yield client
    finally:
        # We don't close the client here as it is a shared pool
        pass

# 初始化时预热连接
redis_client = RedisService.get_client()
