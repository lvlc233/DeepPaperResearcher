import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agent.summary_agent.agent import summary_agent_graph
from agent.summary_agent.schema import SummaryAgentState
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda

def test_summary_agent_compilation():
    """测试 SummaryAgent 图是否可以成功编译"""
    assert summary_agent_graph is not None

@pytest.mark.asyncio
async def test_summary_agent_execution_flow():
    """
    测试 SummaryAgent 的完整执行流程 (Mock LLM 和 Tools)。
    """
    
    # 1. Mock LLM
    async def fake_ainvoke(input, config=None, **kwargs):
        return AIMessage(content="Paper Summary Content")
        
    mock_llm = RunnableLambda(fake_ainvoke)
    
    # 2. Mock read_paper Tool
    with patch("agent.summary_agent.node.read_paper") as mock_read_tool, \
         patch("agent.summary_agent.node.get_llm", return_value=mock_llm):
        
        mock_read_tool.ainvoke = AsyncMock(return_value="Full Paper Text Content...")
        
        # 3. Init State
        initial_state = SummaryAgentState(
            messages=[HumanMessage(content="Summarize this paper")],
            context=[],
            sender="user",
            paper_id="2310.12345", # Arxiv ID
            paper_content=None,
            summary=None,
            language="Chinese"
        )
        
        # 4. Run Graph
        final_state = await summary_agent_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": "mock_thread_2"}}
        )
        
        # 5. Assertions
        
        # check load_paper_node
        assert final_state["paper_content"] == "Full Paper Text Content..."
        
        # check generate_summary_node
        assert final_state["summary"] == "Paper Summary Content"
        assert final_state["messages"][-1].content == "Paper Summary Content"
        assert final_state["sender"] == "SummaryAgent"
