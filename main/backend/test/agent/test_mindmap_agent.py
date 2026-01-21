import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agent.mindmap_agent.agent import mindmap_agent_graph
from agent.mindmap_agent.schema import MindMapAgentState
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda

@pytest.mark.asyncio
async def test_mindmap_agent_compilation():
    assert mindmap_agent_graph is not None

@pytest.mark.asyncio
async def test_mindmap_agent_execution_flow():
    """
    测试 MindMapAgent 的完整执行流程。
    """
    
    # 1. Mock LLM
    async def fake_ainvoke(input, config=None, **kwargs):
        return AIMessage(content="mindmap\n  root((Title))\n    Node1")
        
    mock_llm = RunnableLambda(fake_ainvoke)
    
    # 2. Mock read_paper Tool
    with patch("agent.mindmap_agent.node.read_paper") as mock_read_tool, \
         patch("agent.mindmap_agent.node.get_llm", return_value=mock_llm):
        
        mock_read_tool.ainvoke = AsyncMock(return_value="Full Paper Text Content...")
        
        # 3. Init State
        initial_state = MindMapAgentState(
            messages=[HumanMessage(content="Generate mindmap")],
            context=[],
            sender="user",
            paper_id="2310.12345",
            paper_content=None,
            mindmap_data=None,
            depth=2
        )
        
        # 4. Run Graph
        final_state = await mindmap_agent_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": "mock_thread_mm"}}
        )
        
        # 5. Assertions
        assert final_state["paper_content"] == "Full Paper Text Content..."
        assert "mindmap" in final_state["mindmap_data"]
        assert "root((Title))" in final_state["mindmap_data"]
        assert final_state["sender"] == "MindMapAgent"
