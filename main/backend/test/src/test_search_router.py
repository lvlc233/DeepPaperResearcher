import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from controller.api.app import create_app
from service.search.search_service import SearchService, get_search_service
from controller.api.auth.router import get_current_user
from controller.api.search.schema import SearchResponse, SearchHistoryResponse
from base.pg.entity import Paper, User
from common.model.enums import PaperStatus

@pytest.fixture
def mock_search_service():
    return AsyncMock(spec=SearchService)

@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com")

@pytest.fixture
def client(mock_search_service, mock_user):
    app = create_app()
    
    async def override_get_search_service():
        return mock_search_service
        
    async def override_get_current_user():
        return mock_user
        
    app.dependency_overrides[get_search_service] = override_get_search_service
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return TestClient(app)

def test_search_papers(client, mock_search_service, mock_user):
    user_id = mock_user.id
    
    # Mock response
    mock_resp = SearchResponse(
        total=1,
        items=[
            {
                "id": str(uuid4()),
                "title": "Test Paper",
                "authors": ["Author A"],
                "status": "completed",
                "created_at": datetime.now(),
                "file_key": "test_key",
                "user_id": user_id
            }
        ],
        query_id=uuid4()
    )
    mock_search_service.search_papers.return_value = mock_resp
    
    payload = {
        "query": "Test",
        "page": 1,
        "page_size": 10
    }
    
    resp = client.post(
        "/api/v1/search", 
        json=payload
    )
    
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Test Paper"
    
    mock_search_service.search_papers.assert_called_once()

def test_get_search_history(client, mock_search_service, mock_user):
    user_id = mock_user.id
    
    mock_resp = [
        SearchHistoryResponse(
            id=uuid4(),
            query="Test Query",
            created_at=datetime.now(),
            result_count=5
        )
    ]
    mock_search_service.get_search_history.return_value = mock_resp
    
    resp = client.get(
        "/api/v1/search/history?limit=5"
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["query"] == "Test Query"
    
    mock_search_service.get_search_history.assert_called_once()

def test_clear_search_history(client, mock_search_service, mock_user):
    user_id = mock_user.id
    
    resp = client.delete(
        "/api/v1/search/history"
    )
    
    assert resp.status_code == 204
    mock_search_service.clear_search_history.assert_called_once()
