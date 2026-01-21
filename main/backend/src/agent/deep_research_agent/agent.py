"""
创建时间: 2026-01-02
创建者: LangGraphAgent
描述: DeepResearchAgent 的编排逻辑 (重构为显式图)。
更新记录:
    [2026-01-14:v2.0:重构为显式 StateGraph, 移除 deepagents 黑盒依赖]
"""

from langgraph.graph import StateGraph, END
from .schema import DeepResearchState
from .node import plan_node, research_node, report_node
from ..base.checkpointer import get_checkpointer

def create_deep_research_agent_graph():
    """
    创建并编译 DeepResearchAgent 的运行图。
    流程: Plan -> Research -> Report
    """
    workflow = StateGraph(DeepResearchState)

    # 1. 添加节点
    workflow.add_node("plan", plan_node)
    workflow.add_node("research", research_node)
    workflow.add_node("report", report_node)

    # 2. 定义边
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "research")
    workflow.add_edge("research", "report")
    workflow.add_edge("report", END)

    # 3. 编译图
    checkpointer = get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer)

# 导出已编译的图实例
deep_research_agent = create_deep_research_agent_graph()

