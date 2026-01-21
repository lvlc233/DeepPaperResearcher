import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agent.search_agent.agent import search_agent_graph
from agent.search_agent.schema import SearchAgentState
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

@pytest.mark.asyncio
async def test_search_agent_compilation():
    """测试 SearchAgent 图是否可以成功编译"""
    assert search_agent_graph is not None

@pytest.mark.asyncio
async def test_search_agent_initial_state():
    """测试 SearchAgent 的状态初始化"""
    state = SearchAgentState(
        messages=[HumanMessage(content="test")],
        context=[],
        sender="user",
        search_results=[],
        search_query=None,
        references=[]
    )
    assert state["messages"][0].content == "test"
    assert state["search_results"] == []

@pytest.mark.asyncio
async def test_search_agent_execution_flow():
    """
    测试 SearchAgent 的完整执行流程 (Mock LLM 和 Tools)。
    验证: analyze -> retrieve -> generate 的数据流转。
    """

    pytest.skip("SearchAgent 节点尚未实现(node.py 为 pass)，暂不做端到端流程断言")
    
    # 1. Mock LLM using RunnableLambda
    mock_llm_response_analyze = AIMessage(content="Optimized Query")
    mock_llm_response_generate = AIMessage(content="Final Answer")
    
    call_count = 0
    async def fake_ainvoke(input, config=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_llm_response_analyze
        else:
            return mock_llm_response_generate

    mock_llm = RunnableLambda(fake_ainvoke)
    
    # 2. Mock Tools (用于 retrieve_node)
    # search_local_papers 和 fetch_arxiv
    with patch("agent.search_agent.node.search_local_papers") as mock_local, \
         patch("agent.search_agent.node.fetch_arxiv") as mock_arxiv, \
         patch("agent.search_agent.node.get_llm", return_value=mock_llm):
        
        # 配置 Tool Mock 返回
        mock_local.ainvoke = AsyncMock(return_value="Local Paper Content")
        mock_arxiv.ainvoke = AsyncMock(return_value="Arxiv Paper Content")
        
        # 3. 准备初始状态
        initial_state = SearchAgentState(
            messages=[HumanMessage(content="Help me find papers about LLM")],
            context=[],
            sender="user",
            search_results=[],
            search_query=None,
            references=[]
        )
        
        # 4. 执行图
        # 使用 ainvoke 运行整个流程
        final_state = await search_agent_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": "mock_thread_1"}}
        )
        
        # 5. 验证结果
        
        # 验证 search_query 被正确设置 (来自 analyze_query_node)
        assert final_state["search_query"] == "Optimized Query"
        
        # 验证 search_results 被填充 (来自 retrieve_node)
        assert len(final_state["search_results"]) == 2
        assert final_state["search_results"][0].page_content == "Local Paper Content"
        assert final_state["search_results"][1].page_content == "Arxiv Paper Content"
        
        # 验证最终消息 (来自 generate_node)
        assert isinstance(final_state["messages"][-1], AIMessage)
        assert final_state["messages"][-1].content == "Final Answer"
        assert final_state["sender"] == "SearchAgent"

