
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from controller.api.reader.schema import JobCreateRequest
from service.reader.job_service import JobService
from base.pg.entity import Job, Paper

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid4()
    return user

@pytest.mark.asyncio
async def test_create_job(mock_user):
    # Mock session
    mock_session = AsyncMock()
    service = JobService(mock_session)
    
    # Mock paper lookup
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Paper(id=uuid4(), user_id=mock_user.id)
    mock_session.execute.return_value = mock_result
    
    # Request
    req = JobCreateRequest(job_type="summary", params={"type": "short"})
    
    # Call
    response = await service.create_job(uuid4(), req, mock_user.id)
    
    assert response.job_type == "summary"
    assert response.status == "queued"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_job(mock_user):
    mock_session = AsyncMock()
    service = JobService(mock_session)
    
    job_id = uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Job(
        id=job_id, 
        paper_id=uuid4(), 
        job_type="summary", 
        status="running",
        progress=50,
        created_at=datetime.now()
    )
    mock_session.execute.return_value = mock_result
    
    response = await service.get_job(job_id, mock_user.id)
    
    assert response.id == job_id
    assert response.status == "running"
    assert response.progress == 50.0

@pytest.mark.asyncio
async def test_subscribe_job_events(mock_user):
    mock_session = AsyncMock()
    service = JobService(mock_session)
    
    # Mock permission check
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Job(
        id=uuid4(), 
        paper_id=uuid4(), 
        job_type="summary", 
        status="running",
        created_at=datetime.now()
    )
    mock_session.execute.return_value = mock_result
    
    # Iterate generator
    events = []
    async for event in service.subscribe_job_events(uuid4(), mock_user.id):
        events.append(event)
        if len(events) >= 2: # Test just a few events
            break
            
    assert len(events) > 0
    assert "event: JobStart" in events[0]
