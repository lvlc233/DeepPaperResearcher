import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agent.paper_chat_agent.agent import paper_chat_agent_graph
from agent.paper_chat_agent.schema import InPaperChatState
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda

@pytest.mark.asyncio
async def test_paper_chat_agent_compilation():
    """测试 PaperChatAgent 图是否可以成功编译"""
    assert paper_chat_agent_graph is not None

@pytest.mark.asyncio
async def test_paper_chat_agent_state():
    """测试 PaperChatAgent 的状态定义"""
    state = InPaperChatState(
        messages=[HumanMessage(content="question")],
        context=[],
        sender="user",
        paper_id="1234.5678",
        retrieved_chunks=[],
        citations=[]
    )
    assert state["paper_id"] == "1234.5678"
    assert state["retrieved_chunks"] == []

@pytest.mark.asyncio
async def test_paper_chat_agent_execution_flow():
    """
    测试 PaperChatAgent 的完整执行流程 (Mock LLM 和 Retrieval)。
    """
    
    # 1. Mock LLM
    async def fake_ainvoke(input, config=None, **kwargs):
        return AIMessage(content="Answer based on paper.")
        
    mock_llm = RunnableLambda(fake_ainvoke)
    
    # 2. Patch get_llm in node.py (如果 node.py 使用 get_llm)
    # 或者 Patch ChatOpenAI 类 (因为当前 node.py 直接实例化 ChatOpenAI)
    
    with patch("agent.paper_chat_agent.node.ChatOpenAI", return_value=mock_llm):
        
        # 3. Init State
        initial_state = InPaperChatState(
            messages=[HumanMessage(content="What is this paper about?")],
            context=[],
            sender="user",
            paper_id="mock_paper_id",
            retrieved_chunks=[],
            citations=[]
        )
        
        # 4. Run Graph
        # 我们传入 is_test=True 来触发 node.py 中的 Mock 逻辑
        final_state = await paper_chat_agent_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": "mock_thread_chat", "is_test": True}}
        )
        
        # 5. Assertions
        
        # check retrieve_node (should return mock chunks)
        assert len(final_state["retrieved_chunks"]) > 0
        assert final_state["retrieved_chunks"][0].page_content == "Mock content for testing."
        
        # check generate_node
        assert final_state["messages"][-1].content == "Answer based on paper."
