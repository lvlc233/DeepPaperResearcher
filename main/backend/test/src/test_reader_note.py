import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from base.pg.entity import User
from service.reader.note_service import NoteService
from service.reader.schema import NoteCreateDTO, NoteUpdateDTO
from controller.api.app import app
from controller.api.auth.router import get_current_user
from service.reader.reader_service import get_reader_service

# --- Service Tests ---

@pytest.mark.asyncio
async def test_note_service_crud():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result
    
    service = NoteService(session)
    paper_id = uuid4()
    user_id = uuid4()
    
    # Create
    note_in = NoteCreateDTO(title="Test Note", content="Markdown Content")
    note = await service.create_note(paper_id, user_id, note_in)
    assert note.title == "Test Note"
    assert note.content == "Markdown Content"
    assert note.paper_id == paper_id
    assert note.user_id == user_id
    session.add.assert_called_once()
    session.commit.assert_called()
    
    # Get
    mock_result.scalar_one_or_none.return_value = note
    fetched = await service.get_note(note.id, user_id)
    assert fetched.id == note.id
    
    # Update
    update_in = NoteUpdateDTO(content="Updated Content")
    updated = await service.update_note(note.id, user_id, update_in)
    assert updated.content == "Updated Content"
    
    # Delete
    deleted = await service.delete_note(note.id, user_id)
    assert deleted is True
    session.delete.assert_called()

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
def mock_note_service():
    with patch("controller.api.reader.router.NoteService") as MockService:
        instance = MockService.return_value
        instance.get_notes_by_paper = AsyncMock(return_value=[])
        instance.create_note = AsyncMock()
        instance.update_note = AsyncMock()
        instance.delete_note = AsyncMock(return_value=True)
        yield instance

def test_get_notes_api(client, mock_note_service):
    paper_id = uuid4()
    response = client.get(f"/api/v1/reader/papers/{paper_id}/notes")
    assert response.status_code == 200
    mock_note_service.get_notes_by_paper.assert_called_once()

def test_create_note_api(client, mock_user_obj, mock_note_service):
    paper_id = uuid4()
    note_data = {"title": "New Note", "content": "Content"}
    
    mock_note = {
        "id": uuid4(),
        "paper_id": paper_id,
        "user_id": mock_user_obj.id,
        "title": "New Note",
        "content": "Content",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    mock_note_service.create_note.return_value = mock_note
    
    response = client.post(f"/api/v1/reader/papers/{paper_id}/notes", json=note_data)
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "New Note"
    mock_note_service.create_note.assert_called_once()

def test_update_note_api(client, mock_user_obj, mock_note_service):
    note_id = uuid4()
    update_data = {"content": "Updated"}
    
    mock_note = {
        "id": note_id,
        "paper_id": uuid4(),
        "user_id": mock_user_obj.id,
        "title": "Old",
        "content": "Updated",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    mock_note_service.update_note.return_value = mock_note
    
    response = client.put(f"/api/v1/reader/notes/{note_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "Updated"

def test_delete_note_api(client, mock_note_service):
    note_id = uuid4()
    response = client.delete(f"/api/v1/reader/notes/{note_id}")
    assert response.status_code == 200
    mock_note_service.delete_note.assert_called_once()
