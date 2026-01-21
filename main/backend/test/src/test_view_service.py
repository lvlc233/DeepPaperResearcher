import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from service.reader.view_service import ViewService
from controller.api.reader.schema import AnnotationRequest
from base.pg.entity import Layer, Annotation as AnnotationEntity

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def view_service(mock_session):
    return ViewService(mock_session)

@pytest.mark.asyncio
async def test_create_view(view_service, mock_session):
    paper_id = uuid4()
    user_id = uuid4()
    name = "Test View"
    
    with patch("base.pg.service.ReaderRepository.create_layer") as mock_create:
        mock_layer = Layer(id=uuid4(), paper_id=paper_id, user_id=user_id, name=name, visible=True)
        mock_create.return_value = mock_layer
        
        response = await view_service.create_view(paper_id, name, user_id)
        
        assert response.name == name
        assert response.enable == True
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_add_annotation(view_service, mock_session):
    paper_id = uuid4()
    view_id = uuid4()
    user_id = uuid4()
    
    req = AnnotationRequest(
        type="highlight",
        rect=[{"x": 10.0, "y": 10.0, "w": 100.0, "h": 20.0}],
        content="Important",
        color="#FFFF00"
    )
    
    with patch("base.pg.service.ReaderRepository.get_layer_by_id") as mock_get_layer, \
         patch("base.pg.service.ReaderRepository.create_annotation") as mock_create_ann:
        
        mock_layer = Layer(id=view_id, paper_id=paper_id, user_id=user_id)
        mock_get_layer.return_value = mock_layer
        mock_create_ann.return_value = AnnotationEntity(id=uuid4())
        
        await view_service.add_annotation(paper_id, view_id, req, user_id)
        
        mock_create_ann.assert_called_once()
