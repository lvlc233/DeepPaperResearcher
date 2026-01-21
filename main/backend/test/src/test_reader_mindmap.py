import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from base.pg.entity import MindMap, User
from service.reader.mind_map_service import MindMapService
from service.reader.schema import MindMapCreateDTO, MindMapUpdateDTO, GraphDataDTO, GraphNodeDTO
from controller.api.app import app
from controller.api.auth.router import get_current_user
from service.reader.reader_service import get_reader_service

# --- Service Tests ---

@pytest.mark.asyncio
async def test_mind_map_service_crud():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result
    
    service = MindMapService(session)
    paper_id = uuid4()
    user_id = uuid4()
    
    # Create (get_or_create)
    graph_data = GraphDataDTO(nodes=[GraphNodeDTO(id="1", label="Node1")], edges=[])
    map_in = MindMapCreateDTO(graph_data=graph_data)
    
    # First call: creates new
    mm = await service.get_or_create_mind_map(paper_id, user_id, map_in)
    assert mm.paper_id == paper_id
    assert mm.graph_data.nodes[0].id == "1"
    session.add.assert_called()
    session.commit.assert_called()
    
    # Update
    mock_result.scalar_one_or_none.return_value = mm
    update_data = GraphDataDTO(nodes=[GraphNodeDTO(id="1", label="Updated")], edges=[])
    update_in = MindMapUpdateDTO(graph_data=update_data)
    
    updated = await service.update_mind_map(paper_id, user_id, update_in)
    assert updated.graph_data.nodes[0].label == "Updated"
    session.add.assert_called()

# --- Controller Tests ---

@pytest.fixture
def mock_user_obj():
    return User(id=uuid4(), email="test@example.com", hashed_password="pw")

@pytest.fixture
def client(mock_user_obj):
    async def mock_get_current_user():
        return mock_user_obj
        
    async def mock_get_reader_service():
        mock_service = MagicMock()
        mock_service.db = AsyncMock()
        return mock_service

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_reader_service] = mock_get_reader_service
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_mm_service():
    with patch("controller.api.reader.router.MindMapService") as MockService:
        instance = MockService.return_value
        instance.get_or_create_mind_map = AsyncMock()
        instance.update_mind_map = AsyncMock()
        yield instance

def test_get_mind_map_api(client, mock_user_obj, mock_mm_service):
    paper_id = uuid4()
    mock_mm = MindMap(
        id=uuid4(), paper_id=paper_id, user_id=mock_user_obj.id,
        graph_data={"nodes": [], "edges": []},
        created_at=datetime.now(), updated_at=datetime.now()
    )
    mock_mm_service.get_or_create_mind_map.return_value = mock_mm
    
    response = client.get(f"/api/v1/reader/papers/{paper_id}/graph")
    assert response.status_code == 200
    assert "nodes" in response.json()["data"]["graph_data"]
    mock_mm_service.get_or_create_mind_map.assert_called_once()

def test_update_mind_map_api(client, mock_user_obj, mock_mm_service):
    paper_id = uuid4()
    update_data = {"graph_data": {"nodes": [{"id": "1", "label": "N1"}], "edges": []}}
    
    mock_mm = MindMap(
        id=uuid4(), paper_id=paper_id, user_id=mock_user_obj.id,
        graph_data=update_data["graph_data"],
        created_at=datetime.now(), updated_at=datetime.now()
    )
    mock_mm_service.update_mind_map.return_value = mock_mm
    
    response = client.put(f"/api/v1/reader/papers/{paper_id}/graph", json=update_data)
    assert response.status_code == 200
    assert response.json()["data"]["graph_data"]["nodes"][0]["label"] == "N1"
    mock_mm_service.update_mind_map.assert_called_once()
