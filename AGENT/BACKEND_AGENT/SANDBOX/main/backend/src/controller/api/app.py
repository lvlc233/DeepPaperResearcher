# TODO: 待测试
"""
开发者: BackendAgent
当前版本: api_app_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:api_app_v0_1:注册论文导入路由并在启动时初始化数据库]
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from src.base.pg.service import init_db
from src.controller.api.papers.ingest.router import router as papers_ingest_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("System starting up...")
    init_db()
    yield
    # Shutdown
    logger.info("System shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="DeepPaperResearcher Backend",
        version="0.1.0",
        lifespan=lifespan
    )

    app.include_router(papers_ingest_router, prefix="/api")

    @app.get("/")
    async def root():
        return {"message": "Hello from DeepPaperResearcher Backend!", "status": "running"}

    return app

app = create_app()
