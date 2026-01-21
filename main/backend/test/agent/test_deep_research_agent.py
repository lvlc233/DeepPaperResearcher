import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agent.deep_research_agent.agent import deep_research_agent
from agent.deep_research_agent.schema import DeepResearchState
from langchain_core.messages import HumanMessage, AIMessage

@pytest.mark.asyncio
async def test_deep_research_agent_execution_flow():
    """
    测试重构后的 DeepResearchAgent 完整流程: Plan -> Research -> Report
    """
    
    # 1. Init State
    initial_state = DeepResearchState(
        messages=[HumanMessage(content="Agentic Workflow")],
        context=[],
        sender="user",
        research_topic=None,
        sub_topics=[],
        found_papers=[],
        report_content=None,
        iteration_count=0
    )
    
    # 2. Run Graph
    # 由于节点逻辑主要依靠 mock 数据 (plan_node, research_node) 和 简单的 f-string (report_node)
    # 我们不需要复杂的 LLM Mock，直接运行即可验证数据流转
    
    final_state = await deep_research_agent.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "mock_thread_dra"}}
    )
    
    # 3. Assertions
    
    # Plan Node
    assert final_state["research_topic"] == "Agentic Workflow"
    assert len(final_state["sub_topics"]) == 3
    assert "Agentic Workflow 的最新进展" in final_state["sub_topics"]
    
    # Research Node
    assert len(final_state["found_papers"]) == 3
    assert final_state["found_papers"][0]["title"] == "Paper about Agentic Workflow 的最新进展"
    
    # Report Node
    assert "研究报告: Agentic Workflow" in final_state["report_content"]
    assert "Paper about Agentic Workflow 的最新进展" in final_state["report_content"]
    assert final_state["sender"] == "DeepResearchAgent"

# 保留对 Tools 的独立测试 (如果它们还在被使用或作为组件)
# 注意: 由于重构，node.py 不再直接导出 plan_research 等工具函数，而是作为节点内部逻辑
# 如果需要测试工具函数，应将其移至 tools.py 并导出
# 这里我们主要测试 Graph 的端到端流程

