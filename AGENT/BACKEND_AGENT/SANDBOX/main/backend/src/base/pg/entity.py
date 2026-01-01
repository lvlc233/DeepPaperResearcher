# TODO: 待测试
"""
开发者: BackendAgent
当前版本: pg_entity_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:pg_entity_v0_1:建立 papers 与 ingest_jobs 两个核心实体，支撑 v0.1 论文来源导入任务流转与 PDF 去重]
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from src.common.utils import now_shanghai

class PaperStatus(StrEnum):
    STORED = "STORED"
    FAILED = "FAILED"


class IngestSourceType(StrEnum):
    UPLOAD = "UPLOAD"
    URL = "URL"


class IngestStatus(StrEnum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    FETCHING = "FETCHING"
    CANDIDATES = "CANDIDATES"
    STORED = "STORED"
    FAILED = "FAILED"


class Paper(SQLModel, table=True):
    __tablename__ = "papers"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    sha256: str = Field(index=True, unique=True, max_length=64)
    storage_backend: str = Field(max_length=32)
    storage_key: str = Field(max_length=512)
    size_bytes: int
    mime_type: str = Field(max_length=128)
    status: PaperStatus = Field(default=PaperStatus.STORED, max_length=32)
    created_at: datetime = Field(default_factory=now_shanghai)
    updated_at: datetime = Field(default_factory=now_shanghai)


class IngestJob(SQLModel, table=True):
    __tablename__ = "ingest_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    paper_id: Optional[UUID] = Field(default=None, index=True)
    source_type: IngestSourceType = Field(max_length=32)
    source_url: Optional[str] = Field(default=None, max_length=2048)
    original_filename: Optional[str] = Field(default=None, max_length=512)
    status: IngestStatus = Field(default=IngestStatus.PENDING, max_length=32, index=True)
    candidates_json: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None, max_length=64)
    error_message: Optional[str] = Field(default=None, max_length=2048)
    created_at: datetime = Field(default_factory=now_shanghai)
    updated_at: datetime = Field(default_factory=now_shanghai)
