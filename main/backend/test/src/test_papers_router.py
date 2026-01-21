import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from controller.api.app import create_app
from base.pg.entity import Paper, User
from common.model.enums import PaperStatus
from service.papers.schema import PaperUploadResponse, PaperDTO
from service.papers.paper_service import get_paper_service, PaperService
from service.papers.arxiv_service import ArxivService
from controller.api.papers.router import get_arxiv_service
from controller.api.auth.router import get_current_user


def _fake_upload_file_response(paper_id: str):
    return PaperUploadResponse(paper_id=paper_id, status=PaperStatus.PENDING.value, message="ok")


@pytest.fixture
def mock_paper_service():
    service = AsyncMock(spec=PaperService)
    return service


@pytest.fixture
def mock_arxiv_service():
    service = AsyncMock(spec=ArxivService)
    return service


@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com")


from service.collections.collection_service import CollectionService, get_collection_service

@pytest.fixture
def mock_collection_service():
    return AsyncMock(spec=CollectionService)


@pytest.fixture
def client(mock_paper_service, mock_arxiv_service, mock_collection_service, mock_user):
    app = create_app()
    
    # Override dependencies
    async def override_get_paper_service():
        return mock_paper_service
        
    async def override_get_current_user():
        return mock_user
        
    async def override_get_collection_service():
        return mock_collection_service
        
    app.dependency_overrides[get_paper_service] = override_get_paper_service
    app.dependency_overrides[get_arxiv_service] = lambda: mock_arxiv_service
    app.dependency_overrides[get_collection_service] = override_get_collection_service
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return TestClient(app)


def test_upload_paper_ok(client, mock_paper_service, mock_user):
    paper_id = str(uuid4())
    mock_paper_service.upload_paper.return_value = _fake_upload_file_response(paper_id)

    files = {"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")}
    resp = client.post("/api/v1/papers/upload", files=files)

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["paper_id"] == paper_id
    assert data["status"] == PaperStatus.PENDING.value
    
    # Verify service call with correct user_id
    mock_paper_service.upload_paper.assert_called_once()
    args, kwargs = mock_paper_service.upload_paper.call_args
    assert kwargs["user_id"] == mock_user.id
    assert kwargs["collection_id"] is None


def test_upload_paper_with_collection_id_ok(client, mock_paper_service, mock_user):
    paper_id = str(uuid4())
    mock_paper_service.upload_paper.return_value = _fake_upload_file_response(paper_id)

    collection_id = uuid4()

    files = {"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")}
    resp = client.post(
        "/api/v1/papers/upload",
        files=files,
        data={"collection_id": str(collection_id)},
    )

    assert resp.status_code == 200
    mock_paper_service.upload_paper.assert_called_once()
    args, kwargs = mock_paper_service.upload_paper.call_args
    assert kwargs["user_id"] == mock_user.id
    assert kwargs["collection_id"] == collection_id


def test_get_paper_status_ok(client, mock_paper_service, mock_user):
    paper_id = uuid4()
    paper_dto = PaperDTO(
        id=paper_id,
        user_id=mock_user.id,
        title="t",
        authors=[],
        abstract=None,
        file_key="k",
        file_url=None,
        status=PaperStatus.PENDING,
        created_at="2024-01-01T00:00:00"
    )
    
    mock_paper_service.get_paper_status.return_value = paper_dto

    resp = client.get(f"/api/v1/papers/{paper_id}/status")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["paper_id"] == str(paper_id)
    assert data["status"] == PaperStatus.PENDING.value


def test_get_paper_status_invalid_id(client):
    resp = client.get("/api/v1/papers/not-a-uuid/status")
    assert resp.status_code == 400


def test_arxiv_search_ok(client, mock_arxiv_service):
    from service.papers.schema import PaperInfo
    
    mock_arxiv_service.search_papers.return_value = [
        PaperInfo(title="Test Paper", authors=["Me"], abstract="Test", source_id="123")
    ]
    
    resp = client.get("/api/v1/papers/search/test")
    
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] == 1
    assert data["papers"][0]["title"] == "Test Paper"


