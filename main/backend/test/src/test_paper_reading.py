
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from controller.api.app import create_app
from service.papers.paper_service import PaperService, get_paper_service
from service.papers.schema import PaperDTO
from common.model.enums import PaperStatus
from controller.api.auth.router import get_current_user
from base.pg.entity import User

@pytest.fixture
def mock_paper_service():
    return AsyncMock(spec=PaperService)

@pytest.fixture
def current_user():
    return User(id=uuid4(), username="testuser", email="test@example.com", hashed_password="pw")

@pytest.fixture
def client(mock_paper_service, current_user):
    app = create_app()
    app.dependency_overrides[get_paper_service] = lambda: mock_paper_service
    app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)

def test_get_paper_file_success(client, mock_paper_service, current_user, tmp_path):
    paper_id = uuid4()
    paper_dto = PaperDTO(
        id=paper_id,
        user_id=current_user.id,
        title="Test Paper",
        authors=["Author A"],
        file_key="test.pdf",
        status=PaperStatus.COMPLETED,
        created_at=datetime.now(),
        toc=[{"title": "Intro", "page": 1}]
    )
    
    mock_paper_service.get_paper_status.return_value = paper_dto

    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF")
    mock_paper_service.get_file_path.return_value = pdf_path

    response = client.get(f"/api/v1/papers/{paper_id}/file")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert response.headers["content-disposition"].startswith("inline")

def test_get_paper_file_not_found_record(client, mock_paper_service, current_user):
    paper_id = uuid4()
    mock_paper_service.get_paper_status.return_value = None
    
    response = client.get(f"/api/v1/papers/{paper_id}/file")
    assert response.status_code == 404

def test_get_paper_file_missing_on_disk(client, mock_paper_service, current_user):
    paper_id = uuid4()
    paper_dto = PaperDTO(
        id=paper_id,
        user_id=current_user.id,
        title="Test Paper",
        authors=["Author A"],
        file_key="test.pdf",
        status=PaperStatus.COMPLETED,
        created_at=datetime.now(),
        toc=[]
    )
    mock_paper_service.get_paper_status.return_value = paper_dto
    mock_paper_service.get_file_path.return_value = None
    
    response = client.get(f"/api/v1/papers/{paper_id}/file")
    assert response.status_code == 404

def test_get_paper_detail_with_toc(client, mock_paper_service, current_user):
    paper_id = uuid4()
    toc_data = [{"title": "Introduction", "page": 1, "level": 1}]
    paper_dto = PaperDTO(
        id=paper_id,
        user_id=current_user.id,
        title="Test Paper",
        authors=["Author A"],
        file_key="test.pdf",
        status=PaperStatus.COMPLETED,
        created_at=datetime.now(),
        toc=toc_data
    )
    
    mock_paper_service.get_paper_status.return_value = paper_dto
    
    response = client.get(f"/api/v1/papers/{paper_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["toc"] == toc_data
    expected_base = str(client.base_url).rstrip("/")
    assert data["file_url"] == f"{expected_base}/api/v1/papers/{paper_id}/file"
