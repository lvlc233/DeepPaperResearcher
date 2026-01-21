
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from controller.api.app import app
from base.pg.entity import User, Paper, AgentSession, PaperChunk
from service.reader.summary_service import SummaryService

# Mock EmbeddingService
@pytest.fixture
def mock_embedding_service():
    with patch("base.embedding.embedding_service.EmbeddingService") as MockService:
        instance = MockService.return_value
        instance.primary_model = AsyncMock()
        instance.primary_model.embed_text.return_value = [0.1] * 1536
        yield instance

# Mock ChatOpenAI
@pytest.fixture
def mock_chat_openai():
    with patch("service.reader.summary_service.ChatOpenAI") as MockChat:
        instance = MockChat.return_value
        # Ensure ainvoke is AsyncMock and returns an AIMessage
        from langchain_core.messages import AIMessage
        instance.ainvoke = AsyncMock(return_value=AIMessage(content="Mocked Summary"))
        yield instance

@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        yield

@pytest.fixture
def db_session():
    session = AsyncMock()
    # add is synchronous
    session.add = MagicMock()
    # commit/refresh are async
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    
    # Mock execute result for scalar_one_or_none and scalars().all()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    return session

@pytest.fixture
def client():
    return TestClient(app)

# Mock Agent Graph
@pytest.fixture
def mock_agent_graph():
    with patch("controller.api.chat.router.paper_chat_agent_graph") as MockGraph:
        # astream_events returns an async generator
        async def mock_stream(*args, **kwargs):
            # Simulate "on_chat_model_stream" events
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="Hello ")}
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="World")}
            }
        
        MockGraph.astream_events.side_effect = mock_stream
        yield MockGraph

@pytest.mark.asyncio
async def test_create_summary(client, db_session):
    # 1. Prepare Data
    user = User(username="test_user", email="test@example.com", hashed_password="pw")
    # db_session.add is a mock, so it won't store anything.
    # We need to configure the session to return the paper when queried.
    
    paper = Paper(
        id=uuid4(),
        user_id=user.id,
        title="Test Paper",
        abstract="This is a test abstract.",
        file_key="key",
        status="completed"
    )
    
    # Configure session.execute to return paper when queried
    # The service calls:
    # 1. check existing summary -> return None (default)
    # 2. get paper -> return paper
    
    mock_result_summary = MagicMock()
    mock_result_summary.scalar_one_or_none.return_value = None
    
    mock_result_paper = MagicMock()
    mock_result_paper.scalar_one_or_none.return_value = paper
    
    # side_effect for consecutive calls
    db_session.execute.side_effect = [mock_result_summary, mock_result_paper]
    
    service = SummaryService(db_session)
    from service.reader.schema import SummaryCreateDTO
    
    # Mock _generate_summary_content to bypass LLM/LangChain
    with patch.object(service, '_generate_summary_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Mocked Summary Content"
        
        summary = await service.get_or_create_summary(
            paper.id, 
            SummaryCreateDTO(summary_type="abstract_rewrite")
        )
        
        assert summary.content == "Mocked Summary Content"
        assert summary.paper_id == paper.id
        # Verify it was called
        mock_gen.assert_called_once()

@pytest.mark.asyncio
async def test_chat_flow(client, db_session, mock_embedding_service, mock_agent_graph):
    # 1. Prepare Data
    user = User(id=uuid4(), username="chat_user", email="chat@example.com", hashed_password="pw")
    paper = Paper(
        id=uuid4(),
        user_id=user.id,
        title="Chat Paper",
        abstract="Abstract",
        file_key="key",
        status="completed"
    )
    
    # 2. Create Session
    from controller.api.chat.router import create_session
    from controller.api.chat.schema import ChatSessionCreate

    # create_session calls: session.add, commit, refresh. 
    # Mock refresh to set ID if needed, but uuid4 is usually generated in init or database default.
    # ChatSession model usually generates ID on init if using uuid4 default.
    
    session_in = ChatSessionCreate(agent_type="chat", paper_id=paper.id)
    
    response = await create_session(session_in, db_session, user)
    chat_session = response.data

    assert chat_session.agent_type == "paper_chat"
    assert chat_session.paper_id == paper.id

    # 3. Send Message
    from controller.api.chat.router import send_message
    from controller.api.chat.schema import ChatMessageRequest

    # send_message calls:
    # 1. check session -> return chat_session
    # 2. agent.astream_events
    # 3. save user message
    # 4. save ai message
    
    # Configure execute for session lookup
    mock_result_session = MagicMock()
    mock_result_session.scalar_one_or_none.return_value = chat_session
    
    db_session.execute.return_value = mock_result_session
    # Reset side_effect from previous test or fixture if any
    db_session.execute.side_effect = None 

    req = ChatMessageRequest(content="Hello Paper")

    # Verify response is streaming
    response = await send_message(chat_session.id, req, db_session, user)

    # Iterate stream
    content = ""
    async for line in response.body_iterator:
        if "token" in line:
            # Simple parse
            import json
            data_str = line.split("data: ")[1].strip()
            if data_str:
                content += json.loads(data_str)

    assert "Hello World" in content
