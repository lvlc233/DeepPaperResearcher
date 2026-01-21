"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:定义 SummaryAgentState]
"""

from typing import Optional, TypedDict
from agent.common.schema import BaseRuntimeWithModelConfig


class SummaryAgentState(TypedDict):
    """
    SummaryAgent (总结助手) 的状态定义。
    """
    
    # 论文内容
    paper_content: Optional[str]
    
    # 生成的总结 (输出)
    summary: Optional[str]
    
    
class SummaryAgentRuntimeContext(TypedDict):
    """
    SummaryAgent (总结助手) 的运行时上下文定义。
    """
    llm_config: BaseRuntimeWithModelConfig #模型配置

    paper_id: str # 论文ID

    # summary_
