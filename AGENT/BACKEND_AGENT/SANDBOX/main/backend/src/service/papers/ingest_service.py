# TODO: 待测试
"""
开发者: BackendAgent
当前版本: ingest_service_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:ingest_service_v0_1:实现 v0.1 论文来源导入：上传/URL 下载、网页 PDF 链接提取、去重存储、任务状态流转]
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import httpx
from sqlmodel import Session, select

from src.base.pg.entity import IngestJob, IngestSourceType, IngestStatus, Paper
from src.common.utils import json_dumps, now_shanghai, validate_public_http_url


logger = logging.getLogger(__name__)


class IngestError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class StoredObject:
    sha256: str
    size_bytes: int
    storage_backend: str
    storage_key: str
    mime_type: str


class _PdfLinkExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self._base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]):
        if tag.lower() != "a":
            return
        href = None
        for k, v in attrs:
            if k.lower() == "href":
                href = v
                break
        if not href:
            return

        abs_url = urljoin(self._base_url, href)
        if ".pdf" in abs_url.lower():
            self.links.append(abs_url)


def _storage_dir() -> Path:
    raw = os.environ.get("STORAGE_DIR")
    if raw:
        return Path(raw)
    return Path("./storage")


def _max_pdf_bytes() -> int:
    raw = os.environ.get("MAX_PDF_BYTES")
    if not raw:
        return 50 * 1024 * 1024
    try:
        return int(raw)
    except ValueError:
        return 50 * 1024 * 1024


def _write_pdf_to_storage(stream, size_limit: int) -> StoredObject:
    import hashlib

    storage_backend = "localfs"
    base_dir = _storage_dir()
    base_dir.mkdir(parents=True, exist_ok=True)

    sha = hashlib.sha256()
    total = 0

    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir=str(base_dir), prefix="ingest_", suffix=".tmp") as tmp:
            tmp_path = Path(tmp.name)

            first_chunk = True
            for chunk in stream:
                if not chunk:
                    continue
                if first_chunk:
                    if not is_pdf_magic(chunk[:5]):
                        raise IngestError("NOT_A_PDF", "目标内容不是 PDF")
                    first_chunk = False

                total += len(chunk)
                if total > size_limit:
                    raise IngestError("FILE_TOO_LARGE", "PDF 文件超过大小限制")

                sha.update(chunk)
                tmp.write(chunk)
    except Exception:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    sha256_hex = sha.hexdigest()
    storage_key = f"papers/{sha256_hex[:2]}/{sha256_hex}.pdf"
    dest_path = base_dir / storage_key
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
    else:
        tmp_path.replace(dest_path)

    return StoredObject(
        sha256=sha256_hex,
        size_bytes=total,
        storage_backend=storage_backend,
        storage_key=storage_key,
        mime_type="application/pdf",
    )


def _extract_pdf_links(html_text: str, base_url: str) -> list[str]:
    parser = _PdfLinkExtractor(base_url=base_url)
    parser.feed(html_text)
    deduped: list[str] = []
    seen = set()
    for u in parser.links:
        if u in seen:
            continue
        seen.add(u)
        deduped.append(u)
    return deduped


def _safe_update_job(session: Session, job: IngestJob, **kwargs) -> IngestJob:
    for k, v in kwargs.items():
        setattr(job, k, v)
    job.updated_at = now_shanghai()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


class PaperIngestService:
    def __init__(self, session: Session, http_client: httpx.Client):
        self._session = session
        self._client = http_client

    def create_upload_job(self, filename: Optional[str]) -> IngestJob:
        job = IngestJob(
            source_type=IngestSourceType.UPLOAD,
            original_filename=filename,
            status=IngestStatus.UPLOADING,
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def create_url_job(self, url: str) -> IngestJob:
        job = IngestJob(
            source_type=IngestSourceType.URL,
            source_url=url,
            status=IngestStatus.FETCHING,
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def ingest_upload(self, filename: Optional[str], file_stream) -> IngestJob:
        job = self.create_upload_job(filename=filename)
        try:
            stored = _write_pdf_to_storage(file_stream, size_limit=_max_pdf_bytes())
            paper = self._upsert_paper(stored)
            job = _safe_update_job(
                self._session,
                job,
                paper_id=paper.id,
                status=IngestStatus.STORED,
                error_code=None,
                error_message=None,
            )
            return job
        except IngestError as exc:
            logger.info("upload ingest failed: code=%s message=%s", exc.code, exc.message)
            return _safe_update_job(
                self._session,
                job,
                status=IngestStatus.FAILED,
                error_code=exc.code,
                error_message=exc.message,
            )

    def ingest_url(self, url: str) -> IngestJob:
        job = self.create_url_job(url=url)
        try:
            current = url
            for _ in range(6):
                validate_public_http_url(current)
                with self._client.stream("GET", current, follow_redirects=False) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise IngestError("REDIRECT_WITHOUT_LOCATION", "重定向缺少 Location")
                        current = urljoin(current, location)
                        continue

                    if response.status_code >= 400:
                        raise IngestError("FETCH_FAILED", f"下载失败: HTTP {response.status_code}")

                    content_type = (response.headers.get("content-type") or "").lower()
                    if "text/html" in content_type:
                        html_text = self._read_limited_text(response.iter_bytes(), limit_bytes=1024 * 1024)
                        links = _extract_pdf_links(html_text=html_text, base_url=current)
                        if not links:
                            raise IngestError("NO_PDF_LINK_FOUND", "网页中未提取到 PDF 链接")
                        if len(links) > 1:
                            return _safe_update_job(
                                self._session,
                                job,
                                status=IngestStatus.CANDIDATES,
                                candidates_json=json_dumps(links),
                            )

                        return self._ingest_pdf_from_url(job=job, url=links[0])

                    return self._ingest_pdf_from_iter(job=job, body_iter=response.iter_bytes())

            raise IngestError("TOO_MANY_REDIRECTS", "重定向次数过多")
        except IngestError as exc:
            logger.info("url ingest failed: code=%s message=%s url=%s", exc.code, exc.message, url)
            return _safe_update_job(
                self._session,
                job,
                status=IngestStatus.FAILED,
                error_code=exc.code,
                error_message=exc.message,
            )

    def get_job(self, ingest_id) -> Optional[IngestJob]:
        stmt = select(IngestJob).where(IngestJob.id == ingest_id)
        return self._session.exec(stmt).first()

    def _read_limited_text(self, body_iter, limit_bytes: int) -> str:
        buf = bytearray()
        total = 0
        for chunk in body_iter:
            if not chunk:
                continue
            total += len(chunk)
            if total > limit_bytes:
                break
            buf.extend(chunk)
        return buf.decode("utf-8", errors="ignore")

    def _ingest_pdf_from_url(self, job: IngestJob, url: str) -> IngestJob:
        current = url
        for _ in range(6):
            validate_public_http_url(current)
            with self._client.stream("GET", current, follow_redirects=False) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise IngestError("REDIRECT_WITHOUT_LOCATION", "重定向缺少 Location")
                    current = urljoin(current, location)
                    continue

                if response.status_code >= 400:
                    raise IngestError("FETCH_FAILED", f"下载失败: HTTP {response.status_code}")

                content_type = (response.headers.get("content-type") or "").lower()
                if "text/html" in content_type:
                    raise IngestError("NOT_A_PDF", "URL 指向内容不是 PDF")

                return self._ingest_pdf_from_iter(job=job, body_iter=response.iter_bytes())

        raise IngestError("TOO_MANY_REDIRECTS", "重定向次数过多")

    def _ingest_pdf_from_iter(self, job: IngestJob, body_iter) -> IngestJob:
        stored = _write_pdf_to_storage(body_iter, size_limit=_max_pdf_bytes())
        paper = self._upsert_paper(stored)
        return _safe_update_job(
            self._session,
            job,
            paper_id=paper.id,
            status=IngestStatus.STORED,
            error_code=None,
            error_message=None,
        )

    def _upsert_paper(self, stored: StoredObject) -> Paper:
        stmt = select(Paper).where(Paper.sha256 == stored.sha256)
        existing = self._session.exec(stmt).first()
        if existing:
            return existing

        paper = Paper(
            sha256=stored.sha256,
            storage_backend=stored.storage_backend,
            storage_key=stored.storage_key,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        self._session.add(paper)
        self._session.commit()
        self._session.refresh(paper)
        return paper


_FILENAME_SANITIZE = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_filename(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    trimmed = name.strip()
    if not trimmed:
        return None
    return _FILENAME_SANITIZE.sub("_", trimmed)[:200]


def parse_candidates(candidates_json: Optional[str]) -> Optional[list[str]]:
    if not candidates_json:
        return None
    try:
        data = json.loads(candidates_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    return [str(x) for x in data]
