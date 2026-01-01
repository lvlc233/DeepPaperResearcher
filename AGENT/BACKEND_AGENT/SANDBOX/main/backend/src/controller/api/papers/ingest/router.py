# TODO: 待测试
"""
开发者: BackendAgent
当前版本: ingest_router_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:ingest_router_v0_1:提供论文导入 API：上传、URL 导入、任务查询；对接 service 与统一响应结构]
"""

from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from src.base.pg.service import get_session
from src.business_model.model import PaperIngestResult, PaperIngestStatusResult, UrlIngestRequest
from src.controller.response import APIResponse
from src.service.papers.ingest_service import PaperIngestService, parse_candidates, safe_filename

router = APIRouter(prefix="/papers/ingest", tags=["papers"])


def get_http_client() -> Generator[httpx.Client, None, None]:
    with httpx.Client(timeout=httpx.Timeout(30.0), follow_redirects=False, trust_env=False) as client:
        yield client


@router.post("/upload", response_model=APIResponse[PaperIngestResult])
def ingest_upload(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    http_client: httpx.Client = Depends(get_http_client),
):
    filename = safe_filename(file.filename)
    service = PaperIngestService(session=session, http_client=http_client)
    job = service.ingest_upload(filename=filename, file_stream=_iter_upload_file(file))

    if job.status == "FAILED":
        raise HTTPException(status_code=400, detail=APIResponse.fail(job.error_code or "INGEST_FAILED", job.error_message or "导入失败").model_dump())

    result = PaperIngestResult(
        ingest_id=job.id,
        paper_id=job.paper_id,
        status=str(job.status),
        candidates=parse_candidates(job.candidates_json),
    )
    return APIResponse.ok(result)


@router.post("/url", response_model=APIResponse[PaperIngestResult])
def ingest_url(
    payload: UrlIngestRequest,
    session: Session = Depends(get_session),
    http_client: httpx.Client = Depends(get_http_client),
):
    service = PaperIngestService(session=session, http_client=http_client)
    job = service.ingest_url(url=payload.url)

    if job.status == "FAILED":
        raise HTTPException(status_code=400, detail=APIResponse.fail(job.error_code or "INGEST_FAILED", job.error_message or "导入失败").model_dump())

    result = PaperIngestResult(
        ingest_id=job.id,
        paper_id=job.paper_id,
        status=str(job.status),
        candidates=parse_candidates(job.candidates_json),
    )
    return APIResponse.ok(result)


@router.get("/{ingest_id}", response_model=APIResponse[PaperIngestStatusResult])
def get_ingest_status(
    ingest_id: UUID,
    session: Session = Depends(get_session),
    http_client: httpx.Client = Depends(get_http_client),
):
    service = PaperIngestService(session=session, http_client=http_client)
    job = service.get_job(ingest_id)
    if not job:
        raise HTTPException(status_code=404, detail=APIResponse.fail("NOT_FOUND", "任务不存在").model_dump())

    result = PaperIngestStatusResult(
        ingest_id=job.id,
        paper_id=job.paper_id,
        status=str(job.status),
        error_code=job.error_code,
        error_message=job.error_message,
        candidates=parse_candidates(job.candidates_json),
    )
    return APIResponse.ok(result)


def _iter_upload_file(file: UploadFile, chunk_size: int = 1024 * 1024):
    file.file.seek(0)
    while True:
        chunk = file.file.read(chunk_size)
        if not chunk:
            break
        yield chunk
