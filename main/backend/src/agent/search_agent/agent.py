"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-08 18:35
更新时间: 2026-01-08 18:35
更新记录: 
    [2026-01-08 18:35:v1.0.0:编排 SearchAgent 图结构: analyze -> retrieve -> generate]
"""

from langgraph.graph import StateGraph, END
from agent.search_agent.schema import SearchAgentState
from agent.search_agent.node import (
    init_node,
    base_search_node,
    search_rag_node,
    search_web_node,
    score_papers_node,
    redirect_node,
    search_end_router,
)
from ..base.checkpointer import get_checkpointer

# TODO: 这边不同数据源的搜索的问题我觉得有研究下(例如权重),现在就并发的去搜索吧
def create_search_agent_graph():
    """
    创建并编译 SearchAgent 的运行图。
    """
    workflow = StateGraph(SearchAgentState)

    # 1. 添加节点
    # 初始化
    workflow.add_node("init", init_node)
    # 基础搜索
    workflow.add_node("base_search", base_search_node)
    # RAG搜索
    workflow.add_node("search_rag", search_rag_node)
    # Web搜索
    workflow.add_node("search_web", search_web_node)
    # 评分
    workflow.add_node("score_papers", score_papers_node)
    # 重定向
    workflow.add_node("redirect", redirect_node)

    # 2. 关系
    """
        1.初始化->基础搜索->评分->判断-(需要继续搜索)->重定向->web/rag->评分<-(循环)
        2.判断-(不需要继续搜索)->结束
    """

    workflow.set_entry_point("init")
    workflow.add_edge("init", "base_search")

    workflow.add_edge("base_search", "score_papers")

    workflow.add_conditional_edges("score_papers",search_end_router,
        {
            "redirect": "redirect",
            "END": END,
        }
    )
    # TODO: 这里可以改为并发扇出
    workflow.add_edge("redirect", "search_web")
    workflow.add_edge("redirect", "search_rag")

    workflow.add_edge(["search_web","search_rag"], "score_papers")
    # 3. 编译图
    # 获取 checkpointer (MemorySaver 或 PostgresSaver)
    checkpointer = get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer)

# 导出已编译的图实例
search_agent_graph = create_search_agent_graph()
