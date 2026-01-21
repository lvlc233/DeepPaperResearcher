"""
创建时间: 2026-01-02
创建者: LangGraphAgent
描述: DeepResearchAgent 的状态定义。
"""
from langgraph.graph.message import BaseMessage, add_messages
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from ..base.state import BaseAgentState

class ResearchPaper(TypedDict):
    title: str
    url: str
    summary: str
    relevance_score: float

class DeepResearchState(BaseAgentState):
    """
    DeepResearchAgent 的状态
    """
    
    # 业务字段
    research_topic: Optional[str]  # 研究主题
    sub_topics: Optional[List[str]] # 拆解的子主题/研究方向
    
    found_papers: Annotated[List[ResearchPaper], lambda x, y: x + y] # 收集到的论文 (增量更新)
    
    report_content: Optional[str] # 最终报告内容
    iteration_count: int # 迭代次数 (防止死循环)

class DeepResearchConfig(TypedDict):
    """
    静态配置
    """
    max_iterations: int
    search_depth: int

