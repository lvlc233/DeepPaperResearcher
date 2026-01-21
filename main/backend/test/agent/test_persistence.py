import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from agent.base.checkpointer import get_postgres_checkpointer_context, get_memory_checkpointer

# Define a simple graph for testing
class State(TypedDict):
    messages: Annotated[list, add_messages]

async def node_a(state: State):
    return {"messages": ["A"]}

def create_graph(checkpointer):
    workflow = StateGraph(State)
    workflow.add_node("a", node_a)
    workflow.set_entry_point("a")
    workflow.add_edge("a", END)
    return workflow.compile(checkpointer=checkpointer)

@pytest.mark.asyncio
async def test_memory_checkpointer():
    checkpointer = get_memory_checkpointer()
    graph = create_graph(checkpointer)
    
    config = {"configurable": {"thread_id": "1"}}
    await graph.ainvoke({"messages": []}, config=config)
    
    state = await graph.aget_state(config)
    assert len(state.values["messages"]) == 1
    # Check content since it is converted to a Message object
    assert state.values["messages"][0].content == "A"

@pytest.mark.asyncio
async def test_postgres_checkpointer_mock():
    """
    Mock postgres interactions to verify the checkpointer setup logic
    """
    # Mock psycopg_pool.AsyncConnectionPool and AsyncPostgresSaver
    with patch("agent.base.checkpointer.AsyncConnectionPool") as MockPool, \
         patch("agent.base.checkpointer.AsyncPostgresSaver") as MockSaver:
        
        # Setup mocks
        mock_pool_instance = AsyncMock()
        MockPool.return_value.__aenter__.return_value = mock_pool_instance
        
        mock_saver_instance = AsyncMock()
        MockSaver.return_value = mock_saver_instance
        
        # Run context manager
        async with get_postgres_checkpointer_context() as checkpointer:
            assert checkpointer == mock_saver_instance
            # Verify setup was called
            mock_saver_instance.setup.assert_awaited_once()
            
            # Create graph with this checkpointer
            graph = create_graph(checkpointer)
            assert graph is not None
