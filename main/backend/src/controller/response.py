"""
开发者: BackendAgent
创建时间: 2026年01月10日
描述: 统一响应结构与全局异常处理
"""

from typing import Any, Generic, TypeVar, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from common.utils import get_now_time_china, format_time_china
from common.model.errors import BaseAppException

from loguru import logger

T = TypeVar("T")


CORS_ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

def _build_cors_headers(request: Request) -> Dict[str, str]:
    """
    注释者: BackendAgent(python)
    时间: 2026-01-17 11:10:00
    使用方式: 在全局异常处理器中调用，为错误响应补齐跨域响应头。
    实现梗概: 若请求携带 Origin 且在允许列表内，则回显 Origin 并设置 Allow-Credentials/Vary。
    """
    # TODO: 这个我记得是当初为了解决前端+了权限后对nginx资源访问的问题＋的补丁,但是我感觉好丑陋啊,这样子的实现,尤其是,直接CORS_ALLOWED_ORIGINS写死。后面整理的时候需要考虑怎么处理。
    origin = request.headers.get("origin")
    if not origin:
        return {}

    if origin not in CORS_ALLOWED_ORIGINS:
        return {}

    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }


class Response(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: str = Field(default_factory=lambda: format_time_china(get_now_time_china()))

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "Response[T]":
        return cls(code=200, message=message, data=data, timestamp=format_time_china(get_now_time_china()))

    @classmethod
    def fail(cls, code: int = 400, message: str = "error", data: Any = None) -> "Response[T]":
        # 返回泛型 Response[T] 而不是 Response[None]，避免 Pydantic 校验错误
        # 当失败时，data 可以是 None 或者具体的错误数据
        return cls(code=code, message=message, data=data, timestamp=format_time_china(get_now_time_china()))

async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""

    cors_headers = _build_cors_headers(request)
    
    # 1. 处理自定义业务异常
    if isinstance(exc, BaseAppException):
        logger.warning("业务异常: {message} (code={code})", message=exc.message, code=exc.code)
        return JSONResponse(
            status_code=exc.code if 400 <= exc.code < 600 else 400, # 保持 HTTP 状态码合理
            content=Response.fail(code=exc.code, message=exc.message, data=exc.data).model_dump(),
            headers=cors_headers or None,
        )
        
    # 2. 处理 FastAPI/Starlette HTTP 异常
    if isinstance(exc, StarletteHTTPException):
        logger.warning("HTTP异常: {detail} (status={status})", detail=str(exc.detail), status=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content=Response.fail(code=exc.status_code, message=str(exc.detail)).model_dump(),
            headers=cors_headers or None,
        )

    # 3. 处理参数验证异常
    if isinstance(exc, RequestValidationError):
        logger.warning("参数验证失败: {errors}", errors=str(exc.errors()))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=Response.fail(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                message="参数验证失败", 
                data=exc.errors()
            ).model_dump(),
            headers=cors_headers or None,
        )

    # 4. 处理其他未知异常 (500)
    logger.error("服务器内部错误: {error}", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=Response.fail(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            message="服务器内部错误，请联系管理员"
        ).model_dump(),
        headers=cors_headers or None,
    )
