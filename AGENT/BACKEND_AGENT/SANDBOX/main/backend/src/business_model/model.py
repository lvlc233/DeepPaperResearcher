# TODO: 待测试
"""
开发者: BackendAgent
当前版本: business_model_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:business_model_v0_1:补充论文导入模块对外/对内的业务数据模型（Pydantic），用于 controller/service 层数据传递]
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaperIngestResult(BaseModel):
    ingest_id: UUID
    paper_id: Optional[UUID] = None
    status: str
    candidates: Optional[list[str]] = None


class PaperIngestStatusResult(BaseModel):
    ingest_id: UUID
    paper_id: Optional[UUID] = None
    status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    candidates: Optional[list[str]] = None


class UrlIngestRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
