# TODO: 待测试
"""
开发者: BackendAgent
当前版本: common_utils_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:common_utils_v0_1:提供上海时区时间、sha256、PDF 魔数校验与 URL 安全校验工具，供论文导入模块复用]
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
from datetime import datetime
from typing import Any, Iterable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


_SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def now_shanghai() -> datetime:
    return datetime.now(tz=_SHANGHAI_TZ)


def sha256_hex_from_chunks(chunks: Iterable[bytes]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        if not chunk:
            continue
        digest.update(chunk)
    return digest.hexdigest()


def is_pdf_magic(header_bytes: bytes) -> bool:
    return header_bytes.startswith(b"%PDF-")


def json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def validate_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL_SCHEME_NOT_ALLOWED")

    host = parsed.hostname
    if not host:
        raise ValueError("URL_HOST_MISSING")

    try:
        addr_infos = socket.getaddrinfo(host, None)
    except OSError as exc:
        raise ValueError("URL_DNS_RESOLVE_FAILED") from exc

    for info in addr_infos:
        ip_str = info[4][0]
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError("URL_IP_NOT_PUBLIC")
