
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from service.papers.paper_service import PaperService, PaperProcessingService
from base.pg.entity import Paper, Collection
from common.model.enums import PaperStatus

@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()
    # Mock context manager
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    return mock_session

@pytest.fixture
def mock_async_session_factory(mock_db_session):
    with patch("service.papers.paper_service.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = mock_db_session
        mock_factory.return_value.__aexit__.return_value = None
        yield mock_factory

@pytest.fixture
def mock_paper_repo():
    with patch("service.papers.paper_service.PaperRepository") as mock_repo:
        # Make methods async
        mock_repo.create_paper = AsyncMock()
        mock_repo.get_paper_by_id = AsyncMock()
        mock_repo.update_paper_status = AsyncMock()
        mock_repo.delete_paper = AsyncMock()
        mock_repo.get_user_papers = AsyncMock()
        mock_repo.update_paper_metadata = AsyncMock()
        yield mock_repo


@pytest.fixture
def mock_collection_repo():
    with patch("service.papers.paper_service.CollectionRepository") as mock_repo:
        mock_repo.get_collection_by_id = AsyncMock()
        mock_repo.get_default_collection = AsyncMock()
        mock_repo.create_collection = AsyncMock()
        mock_repo.add_paper_to_collection = AsyncMock()
        yield mock_repo

@pytest.fixture
def mock_settings():
    with patch("service.papers.paper_service.settings") as mock_settings:
        mock_settings.upload_dir = "dummy_dir"
        mock_settings.max_file_size = 1024 * 1024 * 10 # 10MB
        mock_settings.arq_redis_url = "redis://localhost:6379/0"
        yield mock_settings

@pytest.fixture
def mock_aiofiles():
    with patch("service.papers.paper_service.aiofiles") as mock_aio:
        mock_file = AsyncMock()
        mock_aio.open.return_value.__aenter__.return_value = mock_file
        yield mock_aio

@pytest.mark.asyncio
async def test_upload_paper_success(mock_settings, mock_db_session, mock_paper_repo, mock_collection_repo, mock_aiofiles):
    service = PaperService(session=mock_db_session)
    user_id = uuid4()
    file_content = b"%PDF-1.4 content"
    filename = "test.pdf"
    
    # Mock create_paper result
    mock_paper = Paper(id=uuid4(), user_id=user_id, title=filename, status=PaperStatus.PENDING)
    mock_paper_repo.create_paper.return_value = mock_paper

    default_collection = Collection(id=uuid4(), user_id=user_id, name="默认收藏夹", is_default=True)
    mock_collection_repo.get_default_collection.return_value = default_collection
    
    with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False), patch.object(service, "_trigger_process_task", new=AsyncMock()):
        response = await service.upload_paper(file_content, filename, user_id)
    
    assert response.status == PaperStatus.PENDING.value
    mock_paper_repo.create_paper.assert_called_once()
    mock_aiofiles.open.assert_called_once()
    mock_collection_repo.add_paper_to_collection.assert_called_once_with(mock_db_session, default_collection.id, mock_paper.id)


@pytest.mark.asyncio
async def test_upload_paper_specified_collection_ok(
    mock_settings,
    mock_db_session,
    mock_paper_repo,
    mock_collection_repo,
    mock_aiofiles,
):
    service = PaperService(session=mock_db_session)
    user_id = uuid4()
    file_content = b"%PDF-1.4 content"
    filename = "test.pdf"

    target_collection_id = uuid4()
    target_collection = Collection(id=target_collection_id, user_id=user_id, name="c", is_default=False)
    mock_collection_repo.get_collection_by_id.return_value = target_collection

    mock_paper = Paper(id=uuid4(), user_id=user_id, title=filename, status=PaperStatus.PENDING)
    mock_paper_repo.create_paper.return_value = mock_paper

    with (
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=False),
        patch.object(service, "_trigger_process_task", new=AsyncMock()),
    ):
        response = await service.upload_paper(
            file_content,
            filename,
            user_id,
            collection_id=target_collection_id,
        )

    assert response.status == PaperStatus.PENDING.value
    mock_collection_repo.add_paper_to_collection.assert_called_once_with(mock_db_session, target_collection_id, mock_paper.id)
    assert mock_collection_repo.get_default_collection.await_count == 0


@pytest.mark.asyncio
async def test_upload_paper_specified_collection_not_found(
    mock_settings,
    mock_db_session,
    mock_paper_repo,
    mock_collection_repo,
    mock_aiofiles,
):
    service = PaperService(session=mock_db_session)
    user_id = uuid4()

    mock_collection_repo.get_collection_by_id.return_value = None

    with pytest.raises(ValueError, match="收藏夹不存在或无权访问"):
        await service.upload_paper(
            b"%PDF-1.4 content",
            "test.pdf",
            user_id,
            collection_id=uuid4(),
        )

    assert mock_paper_repo.create_paper.await_count == 0
    assert mock_aiofiles.open.call_count == 0

@pytest.mark.asyncio
async def test_upload_paper_invalid_file(mock_settings, mock_db_session):
    service = PaperService(session=mock_db_session)
    user_id = uuid4()
    
    # Invalid content
    with pytest.raises(ValueError, match="文件验证失败"):
        await service.upload_paper(b"invalid content", "test.pdf", user_id)
        
    # Invalid extension
    with pytest.raises(ValueError, match="文件验证失败"):
        await service.upload_paper(b"%PDF...", "test.txt", user_id)

@pytest.mark.asyncio
async def test_process_pdf_success(mock_settings, mock_async_session_factory, mock_paper_repo, mock_db_session):
    service = PaperProcessingService()
    paper_id = uuid4()
    
    # Mock Paper
    mock_paper = Paper(id=paper_id, file_key="test_key", status=PaperStatus.PENDING)
    mock_paper_repo.get_paper_by_id.return_value = mock_paper
    
    # Mock internal methods
    with patch.object(service, "_parse_pdf", return_value="parsed text") as mock_parse, \
         patch.object(service, "_extract_metadata", return_value={"title": "Test Title", "authors": ["Author"]}) as mock_meta, \
         patch.object(service, "_split_text", return_value=["chunk1", "chunk2"]) as mock_split, \
         patch.object(service, "_generate_embeddings", return_value=[[0.1]*1536, [0.2]*1536]) as mock_embed, \
         patch.object(service, "_save_chunks") as mock_save, \
         patch.object(service, "_update_paper_after_processing") as mock_update_after, \
         patch("pathlib.Path.exists", return_value=True):
        
        result = await service.process_pdf(paper_id)
        
        assert result is True
        mock_parse.assert_called_once()
        mock_split.assert_called_once()
        mock_embed.assert_called_once()
        mock_save.assert_called_once()
        mock_update_after.assert_called_once()
        
        # Verify status updates
        # Called once for PROCESSING
        mock_paper_repo.update_paper_status.assert_any_call(mock_db_session, paper_id, PaperStatus.PROCESSING)
