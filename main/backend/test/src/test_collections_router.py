
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from controller.api.app import create_app
from service.collections.collection_service import CollectionService, get_collection_service
from controller.api.collections.schema import CollectionResponse
from service.papers.schema import PaperDTO
from common.model.enums import PaperStatus
from controller.api.auth.router import get_current_user
from base.pg.entity import User

@pytest.fixture
def mock_collection_service():
    return AsyncMock(spec=CollectionService)

@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com")


@pytest.fixture
def client(mock_collection_service, mock_user):
    app = create_app()
    
    async def override_get_collection_service():
        return mock_collection_service

    async def override_get_current_user():
        return mock_user
        
    app.dependency_overrides[get_collection_service] = override_get_collection_service
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return TestClient(app)

def _fake_collection_response(collection_id=None, user_id=None, name="Test Collection"):
    if not collection_id:
        collection_id = uuid4()
    if not user_id:
        user_id = uuid4()
    
    return CollectionResponse(
        id=collection_id,
        user_id=user_id,
        name=name,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

def test_create_collection(client, mock_collection_service, mock_user):
    user_id = mock_user.id
    collection_id = uuid4()
    
    mock_resp = _fake_collection_response(collection_id, user_id, "New Collection")
    mock_collection_service.create_collection.return_value = mock_resp
    
    payload = {
        "name": "New Collection"
    }
    
    resp = client.post(
        "/api/v1/collections", 
        json=payload
    )
    
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["collection_id"] == str(collection_id)
    assert data["name"] == "New Collection"
    
    mock_collection_service.create_collection.assert_called_once()

def test_get_collections(client, mock_collection_service, mock_user):
    user_id = mock_user.id
    mock_resps = [
        _fake_collection_response(uuid4(), user_id, "C1"),
        _fake_collection_response(uuid4(), user_id, "C2")
    ]
    mock_collection_service.get_user_collections.return_value = mock_resps
    
    resp = client.get(
        "/api/v1/collections"
    )
    
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    assert data[0]["name"] == "C1"
    assert "total" in data[0]
    mock_collection_service.get_user_collections.assert_called_once()

def test_update_collection(client, mock_collection_service, mock_user):
    user_id = mock_user.id
    collection_id = uuid4()
    
    mock_resp = _fake_collection_response(collection_id, user_id, "Updated Name")
    mock_collection_service.update_collection.return_value = mock_resp
    
    payload = {"new_name": "Updated Name"}
    
    resp = client.patch(
        f"/api/v1/collections/{collection_id}",
        params=payload
    )
    
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Updated Name"

def test_delete_collection(client, mock_collection_service):
    mock_collection_service.delete_collection.return_value = True
    
    resp = client.delete(
        f"/api/v1/collections/{uuid4()}"
    )
    
    assert resp.status_code == 200

def test_remove_paper(client, mock_collection_service):
    mock_collection_service.remove_paper_from_collection.return_value = True
    
    resp = client.delete(
        f"/api/v1/collections/{uuid4()}/papers/{uuid4()}"
    )
    
    assert resp.status_code == 200

def test_move_paper_ok(client, mock_collection_service, mock_user):
    paper_id = uuid4()
    collection_id = uuid4()
    
    mock_collection_service.move_paper.return_value = True
    
    resp = client.patch(
        f"/api/v1/collections/{collection_id}/papers/move/{paper_id}"
    )
    
    assert resp.status_code == 200
    assert resp.json()["data"] is True
    
    mock_collection_service.move_paper.assert_called_once()
    args, kwargs = mock_collection_service.move_paper.call_args
    assert args[0] == paper_id
    assert args[1] == collection_id
    assert args[2] == mock_user.id

def test_move_paper_fail(client, mock_collection_service):
    paper_id = uuid4()
    collection_id = uuid4()
    
    mock_collection_service.move_paper.return_value = False
    
    resp = client.patch(
        f"/api/v1/collections/{collection_id}/papers/move/{paper_id}"
    )
    
    assert resp.status_code == 400
