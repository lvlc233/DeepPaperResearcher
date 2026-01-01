# TODO: 待测试
"""
开发者: BackendAgent
当前版本: test_paper_ingest_v0_1
创建时间: 2026-01-02
更新时间: 2026-01-02
更新记录:
    [2026-01-02:test_paper_ingest_v0_1:覆盖论文导入成功（上传）与失败（URL HTML 无 PDF 链接）两条路径]
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import httpx
from fastapi.testclient import TestClient


_TMP = tempfile.TemporaryDirectory()
_DB_PATH = Path(_TMP.name) / "test.db"
_STORAGE_DIR = Path(_TMP.name) / "storage"

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"
os.environ["STORAGE_DIR"] = _STORAGE_DIR.as_posix()


class PaperIngestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.controller.api.app import create_app
        from src.controller.api.papers.ingest.router import get_http_client

        cls.get_http_client = get_http_client
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_upload_success(self):
        pdf_bytes = (
            b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
            b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"trailer\n<<>>\n%%EOF\n"
        )
        resp = self.client.post(
            "/api/papers/ingest/upload",
            files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["success"])
        self.assertIn("ingest_id", payload["data"])
        self.assertIn("status", payload["data"])
        self.assertEqual(payload["data"]["status"], "STORED")

    def test_url_html_no_pdf_link_failed(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if str(request.url) == "https://example.com/page":
                return httpx.Response(
                    200,
                    headers={"content-type": "text/html; charset=utf-8"},
                    text="<html><body><a href='https://example.com/x'>x</a></body></html>",
                )
            return httpx.Response(404)

        transport = httpx.MockTransport(handler)

        def override_client():
            with httpx.Client(transport=transport, follow_redirects=False, trust_env=False) as client:
                yield client

        self.app.dependency_overrides[self.get_http_client] = override_client
        try:
            resp = self.client.post("/api/papers/ingest/url", json={"url": "https://example.com/page"})
            self.assertEqual(resp.status_code, 400)
            detail = resp.json()["detail"]
            self.assertFalse(detail["success"])
            self.assertEqual(detail["error"]["code"], "NO_PDF_LINK_FOUND")
        finally:
            self.app.dependency_overrides.pop(self.get_http_client, None)


if __name__ == "__main__":
    unittest.main()
