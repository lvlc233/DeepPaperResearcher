'''
开发者: BackendAgent
当前版本: v1.0_neo4j_init
创建时间: 2026-01-14 14:35:00
更新时间: 2026-01-14 14:35:00
更新记录: 
    [2026-01-14 14:35:00:v1.0_neo4j_init:初始化Neo4j客户端连接]
'''

from typing import Optional, AsyncGenerator
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from base.config import settings
from loguru import logger
from contextlib import asynccontextmanager

class Neo4jService:
    _driver: Optional[AsyncDriver] = None

    @classmethod
    def get_driver(cls) -> AsyncDriver:
        if cls._driver is None:
            logger.info(f"Creating Neo4j driver: {settings.neo4j_url}")
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_url, 
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return cls._driver

    @classmethod
    async def close(cls):
        if cls._driver:
            await cls._driver.close()
            logger.info("Neo4j driver closed")
            cls._driver = None

    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        driver = cls.get_driver()
        async with driver.session() as session:
            yield session

async def get_neo4j_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for Neo4j session.
    """
    async with Neo4jService.get_session() as session:
        yield session

# 初始化时预热
neo4j_driver = Neo4jService.get_driver()
