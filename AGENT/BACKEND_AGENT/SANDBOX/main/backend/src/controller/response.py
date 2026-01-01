
# TODO: 待测试
"""
开发者: BackendAgent
当前版本: controller_response_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:controller_response_v0_1:统一 API 响应结构，支持 success/data/error 三段式返回]
"""

from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel


class APIError(BaseModel):
    code: str
    message: str


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[APIError] = None

    @classmethod
    def ok(cls, data: T) -> "APIResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message: str) -> "APIResponse[None]":
        return cls(success=False, error=APIError(code=code, message=message))
