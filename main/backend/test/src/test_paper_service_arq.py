import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from pathlib import Path
from service.papers.paper_service import PaperService
from common.model.enums import PaperStatus
from base.config import settings

@pytest.mark.asyncio
async def test_upload_paper_triggers_arq():
    # Mock session
    session = AsyncMock()
    
    # Initialize service
    service = PaperService(session)
    
    # Mock dependencies
    writer = AsyncMock()
    writer.wait_closed = AsyncMock()
    writer.close = MagicMock()

    with patch("service.papers.paper_service.aiofiles.open") as mock_open, \
         patch("service.papers.paper_service.PaperRepository") as mock_repo, \
         patch("service.papers.paper_service.CollectionRepository") as mock_collection_repo, \
         patch("service.papers.paper_service.asyncio.open_connection", new=AsyncMock(return_value=(AsyncMock(), writer))), \
         patch("service.papers.paper_service.create_pool") as mock_create_pool:
        
        # Setup mocks
        mock_file_handle = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file_handle
        
        mock_paper = MagicMock()
        mock_paper.id = uuid4()
        mock_paper.status = PaperStatus.PENDING
        # Fix: Make create_paper an AsyncMock
        mock_repo.create_paper = AsyncMock(return_value=mock_paper)
        
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool

        mock_collection_repo.get_default_collection = AsyncMock(return_value=MagicMock(id=uuid4()))
        mock_collection_repo.add_paper_to_collection = AsyncMock()
        
        # Call upload_paper
        user_id = uuid4()
        file_content = b"%PDF-1.4 test"
        filename = "test.pdf"
        
        response = await service.upload_paper(file_content, filename, user_id)
        
        # Verify result
        assert response.paper_id == str(mock_paper.id)
        assert response.status == PaperStatus.PENDING.value
        
        # Verify Arq triggered
        mock_create_pool.assert_called_once()
        mock_pool.enqueue_job.assert_called_once_with('process_pdf_task', str(mock_paper.id))
        mock_pool.close.assert_called_once()

@pytest.mark.asyncio
async def test_trigger_process_task_error_handling():
    # Verify that error in triggering task does not raise exception
    session = AsyncMock()
    service = PaperService(session)
    
    writer = AsyncMock()
    writer.wait_closed = AsyncMock()
    writer.close = MagicMock()

    with patch("service.papers.paper_service.asyncio.open_connection", new=AsyncMock(return_value=(AsyncMock(), writer))), \
         patch("service.papers.paper_service.create_pool", side_effect=Exception("Redis error")):
        # Should not raise exception
        await service._trigger_process_task(uuid4(), Path("test.pdf"))
