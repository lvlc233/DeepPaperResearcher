"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:编排 MindMapAgent 图结构]
"""

from langgraph.graph import StateGraph, END
from .schema import MindMapAgentState
from .node import load_paper_node, generate_mindmap_node
from ..base.checkpointer import get_checkpointer

def create_mindmap_agent_graph():
    """
    创建并编译 MindMapAgent 的运行图。
    """
    workflow = StateGraph(MindMapAgentState)

    workflow.add_node("load_paper", load_paper_node)
    workflow.add_node("generate_mindmap", generate_mindmap_node)

    workflow.set_entry_point("load_paper")
    workflow.add_edge("load_paper", "generate_mindmap")
    workflow.add_edge("generate_mindmap", END)

    checkpointer = get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer)

mindmap_agent_graph = create_mindmap_agent_graph()
