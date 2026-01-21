'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 07:43
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:统一版本号]
    [2026年01月02日 08:54:v0.1_app_with_papers:注册papers路由，支持论文获取功能]
'''

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from loguru import logger

# 导入papers路由
from controller.api.papers.router import router as papers_router
from controller.api.auth.router import router as auth_router, users_router
from controller.api.reader.router import router as reader_router
from controller.api.collections.router import router as collections_router
from controller.api.search.router import router as search_router
from controller.api.settings.settings_router import router as settings_router
from controller.api.jobs.router import router as jobs_router

# 导入异常处理器
from controller.response import global_exception_handler
from common.logger import setup_logging
from base.pg.service import engine
from base.redis.service import RedisService
from base.neo4j.service import Neo4jService

# 配置日志
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("System starting up...")
   
    yield
    # Shutdown
    logger.info("System shutting down...")

    await engine.dispose()
    logger.info("Database connection pool disposed")
    
    await RedisService.close()
    await Neo4jService.close()

def create_app() -> FastAPI:
    app = FastAPI(
        title="DeepPaperResearcher Backend",
        version="0.1.0",
        lifespan=lifespan,
        description="基于 LangGraph 的 AI 辅助论文研究与管理平台 API"
    )
    # 跨域
    app.add_middleware(
        CORSMiddleware,
        # 当 allow_credentials=True 时，allow_origins 不能包含 "*"，必须显式指定域名
        # TODO: 这边也是给nginx做适配来着的,也是后面要考虑的问题。
        allow_origins=[
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "http://localhost:5173", # Vite 默认端口，以防万一
            "http://127.0.0.1:5173"
        ],
        allow_credentials=True,
        allow_methods=["*"],  # 关键：允许所有HTTP方法
        allow_headers=["*"],  # 关键：允许所有请求头
    )
    # 注册全局异常处理器
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(StarletteHTTPException, global_exception_handler)
    app.add_exception_handler(RequestValidationError, global_exception_handler)

    # 注册papers路由
    logger.info("注册papers路由")
    app.include_router(papers_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(reader_router, prefix="/api/v1")
    app.include_router(collections_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(settings_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": "Hello from DeepPaperResearcher Backend!", "status": "running", "version": "0.1.0"}

    return app

app = create_app()
