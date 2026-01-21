"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-08 18:48
更新时间: 2026-01-08 18:48
更新记录: 
    [2026-01-08 18:48:v1.0.0:编排 InPaperChatAgent 图结构: retrieve -> generate]
"""

from langgraph.graph import StateGraph, END
from .schema import InPaperChatState
from .node import retrieve_paper_chunks_node, generate_answer_node
from ..base.checkpointer import get_checkpointer

def create_paper_chat_agent_graph():
    """
    创建并编译 InPaperChatAgent 的运行图。
    """
    workflow = StateGraph(InPaperChatState)

    # 1. 添加节点
    workflow.add_node("retrieve", retrieve_paper_chunks_node)
    workflow.add_node("generate", generate_answer_node)

    # 2. 定义边
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # 3. 编译图
    checkpointer = get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer)

# 导出已编译的图实例
paper_chat_agent_graph = create_paper_chat_agent_graph()
