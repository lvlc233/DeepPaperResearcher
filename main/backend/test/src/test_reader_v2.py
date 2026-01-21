import pytest
import sys
import os
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from controller.api.app import create_app
from service.reader.reader_service import get_reader_service, ReaderService
from controller.api.reader.router import (
    get_toc_service, get_view_service, get_note_service, 
    get_summary_service, get_mind_map_service, get_history_service, get_job_service
)
from service.reader.toc_service import TocService
from service.reader.view_service import ViewService
from service.reader.note_service import NoteService
from service.reader.summary_service import SummaryService
from service.reader.mind_map_service import MindMapService
from service.reader.history_service import HistoryService
from service.reader.job_service import JobService

from controller.api.reader import schema
from service.reader import schema as service_schema
from controller.api.auth.router import get_current_user
from base.pg.entity import User

@pytest.fixture
def mock_reader_service():
    return AsyncMock(spec=ReaderService)

@pytest.fixture
def mock_toc_service():
    return AsyncMock(spec=TocService)

@pytest.fixture
def mock_view_service():
    return AsyncMock(spec=ViewService)

@pytest.fixture
def mock_note_service():
    return AsyncMock(spec=NoteService)

@pytest.fixture
def mock_summary_service():
    return AsyncMock(spec=SummaryService)

@pytest.fixture
def mock_mind_map_service():
    return AsyncMock(spec=MindMapService)

@pytest.fixture
def mock_history_service():
    return AsyncMock(spec=HistoryService)

@pytest.fixture
def mock_job_service():
    return AsyncMock(spec=JobService)

@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com", username="testuser", role="user")

@pytest.fixture
def client(
    mock_reader_service, mock_toc_service, mock_view_service, 
    mock_note_service, mock_summary_service, mock_mind_map_service,
    mock_history_service, mock_job_service, mock_user
):
    app = create_app()
    app.dependency_overrides[get_reader_service] = lambda: mock_reader_service
    app.dependency_overrides[get_toc_service] = lambda: mock_toc_service
    app.dependency_overrides[get_view_service] = lambda: mock_view_service
    app.dependency_overrides[get_note_service] = lambda: mock_note_service
    app.dependency_overrides[get_summary_service] = lambda: mock_summary_service
    app.dependency_overrides[get_mind_map_service] = lambda: mock_mind_map_service
    app.dependency_overrides[get_history_service] = lambda: mock_history_service
    app.dependency_overrides[get_job_service] = lambda: mock_job_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return TestClient(app)

def test_get_paper_meta(client, mock_reader_service):
    paper_id = uuid4()
    mock_data = service_schema.PaperReaderMeta(
        paper_id=paper_id,
        file_url="http://example.com/file.pdf",
        views=[],
        notes=[],
        history=[],
        jobs=[]
    )
    mock_reader_service.get_paper_meta.return_value = mock_data
    
    resp = client.get(f"/api/v1/papers/{paper_id}/meta")
    assert resp.status_code == 200, f"Failed: {resp.status_code}, {resp.text}"
    assert resp.json()["code"] == 200
    assert resp.json()["data"]["paper_id"] == str(paper_id)

def test_get_toc(client, mock_toc_service):
    paper_id = uuid4()
    # Use service_schema for DTOs
    mock_toc = service_schema.Toc(items=[service_schema.TocItem(title="Intro", page=1)])
    mock_toc_service.get_toc.return_value = mock_toc
    
    resp = client.get(f"/api/v1/papers/{paper_id}/toc")
    assert resp.status_code == 200
    assert resp.json()["data"]["items"][0]["title"] == "Intro"

def test_get_views(client, mock_view_service):
    paper_id = uuid4()
    mock_views = [service_schema.View(id=uuid4(), name="Default", visible=True, annotations=[])]
    mock_view_service.get_views.return_value = mock_views
    
    resp = client.get(f"/api/v1/papers/{paper_id}/views")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

def test_get_notes(client, mock_note_service):
    paper_id = uuid4()
    mock_data = [
        service_schema.NoteMeta(id=uuid4(), title="Note 1", page=1, created_at=datetime.now())
    ]
    mock_note_service.get_notes_meta.return_value = mock_data
    
    resp = client.get(f"/api/v1/papers/{paper_id}/notes")
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 1

def test_get_note_detail(client, mock_note_service):
    paper_id = uuid4()
    note_id = uuid4()
    mock_data = service_schema.NoteDTO(
        id=note_id,
        paper_id=paper_id,
        user_id=uuid4(),
        title="Note Detail",
        page=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        content="Note content"
    )
    mock_note_service.get_note_detail.return_value = mock_data
    
    resp = client.get(f"/api/v1/papers/{paper_id}/notes/{note_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == str(note_id)
    assert resp.json()["data"]["content"] == "Note content"

def test_get_ai_summary(client, mock_summary_service):
    paper_id = uuid4()
    mock_data = service_schema.AISummary(summary_config={"abstract": "Summary"})
    mock_summary_service.get_ai_summary.return_value = mock_data
    
    resp = client.get(f"/api/v1/papers/{paper_id}/ai/summary")
    assert resp.status_code == 200
    assert resp.json()["data"]["summary_config"]["abstract"] == "Summary"

def test_get_mind_map(client, mock_mind_map_service):
    paper_id = uuid4()
    mock_data = service_schema.MindMap(
        nodes=[service_schema.MindMapNode(id="1", label="Node 1")],
        edges=[]
    )
    mock_mind_map_service.get_mind_map_data.return_value = mock_data
    
    resp = client.get(f"/api/v1/papers/{paper_id}/ai/mind_map")
    assert resp.status_code == 200
    assert len(resp.json()["data"]["nodes"]) == 1

def test_get_jobs(client, mock_job_service):
    paper_id = uuid4()
    mock_data = [
        service_schema.Job(
            id=uuid4(), 
            job_type="summary", 
            status="running", 
            created_at=datetime.now(),
            progress=0.5
        )
    ]
    mock_job_service.get_jobs.return_value = mock_data
    
    resp = client.get(f"/api/v1/papers/{paper_id}/jobs")
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 1
