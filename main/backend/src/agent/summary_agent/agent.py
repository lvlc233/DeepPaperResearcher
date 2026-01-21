"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:编排 SummaryAgent 图结构: load_paper -> generate_summary]
"""

from langgraph.graph import StateGraph, END
from agent.summary_agent.schema import SummaryAgentState
from agent.summary_agent.node import load_paper_node, generate_summary_node
from agent.base.checkpointer import get_checkpointer

def create_summary_agent_graph():
    """
    创建并编译 SummaryAgent 的运行图。
    """
    workflow = StateGraph(SummaryAgentState)

    # 1. 添加节点
    workflow.add_node("load_paper", load_paper_node)
    workflow.add_node("generate_summary", generate_summary_node)

    # 2. 定义边
    workflow.set_entry_point("load_paper")
    workflow.add_edge("load_paper", "generate_summary")
    workflow.add_edge("generate_summary", END)

    # 3. 编译图
    checkpointer = get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer)

# 导出已编译的图实例
summary_agent_graph = create_summary_agent_graph()
