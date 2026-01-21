
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from controller.api.search.schema import SearchRequest, SearchFilter
from service.search.search_service import SearchService
from service.papers.paper_service import PaperService
from controller.api.papers.schema import PapersUploadWebRequest, PapersUploadResponse
from service.papers.schema import PaperUploadResponse as ServicePaperUploadResponse
from common.model.enums import PaperStatus
from base.arxiv.schema import ArxivPaperInfo

@pytest.mark.asyncio
async def test_search_papers_arxiv(mock_search_service, mock_user):
    # Mock ArxivService
    mock_arxiv_service = AsyncMock()
    mock_arxiv_service.search_papers.return_value = [
        ArxivPaperInfo(
            title="Test Arxiv Paper",
            authors=["Author A"],
            abstract="Abstract",
            paper_url="http://arxiv.org/abs/123",
            pdf_url="http://arxiv.org/pdf/123.pdf",
            published_date=datetime.now(),
            categories=["cs.AI"],
            source_id="123"
        )
    ]
    
    # Request
    request = SearchRequest(
        query="Test",
        page=1,
        limit=10,
        filters=SearchFilter(source="arXiv")
    )
    
    # Call
    # Note: mock_search_service is a Mock object usually in pytest-mock fixtures,
    # but here we want to test the REAL SearchService logic with MOCKED dependencies.
    # So we should instantiate SearchService with a mock session.
    
    mock_session = AsyncMock()
    service = SearchService(mock_session)
    
    # We need to mock _save_search_history if it uses session
    service._save_search_history = AsyncMock(return_value=uuid4())
    
    response = await service.search_papers(mock_user.id, request, mock_arxiv_service)
    
    assert response.total == 1
    assert response.items[0].source == "arXiv"
    assert response.items[0].title == "Test Arxiv Paper"
    mock_arxiv_service.search_papers.assert_called_once()

@pytest.mark.asyncio
async def test_upload_papers_from_web(mock_paper_service):
    # We want to test the logic inside PaperService.upload_papers_from_web
    # So we need a real PaperService instance (or close to it) with mocked dependencies.
    # But mock_paper_service is likely a Mock object.
    # Let's use patch to mock httpx
    
    # Instantiate service
    mock_session = AsyncMock()
    service = PaperService(mock_session)
    
    # Mock upload_paper method
    service.upload_paper = AsyncMock(return_value=ServicePaperUploadResponse(
        paper_id=str(uuid4()),
        status="pending",
        message="ok"
    ))
    
    req = PapersUploadWebRequest(urls=["http://example.com/test.pdf"])
    
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__aenter__.return_value
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/pdf"}
        mock_resp.content = b"pdf_content"
        mock_client.get.return_value = mock_resp
        
        responses = await service.upload_papers_from_web(req, uuid4())
        
        assert len(responses) == 1
        assert responses[0].title == "test.pdf"
        assert responses[0].status == "pending"
        service.upload_paper.assert_called_once()
