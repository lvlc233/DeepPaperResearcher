"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-08 18:40
更新时间: 2026-01-08 18:40
更新记录: 
    [2026-01-08 18:40:v1.0.0:定义 InPaperChatState, 继承 BaseAgentState, 增加 paper_id 和 chunks]
"""

from typing import Annotated, List, Optional, Dict, Any
from ..base.state import BaseAgentState
from langchain_core.documents import Document

class InPaperChatState(BaseAgentState):
    """
    InPaperChatAgent (单篇论文问答) 的状态定义。
    """
    
    # 当前聚焦的论文 ID
    paper_id: str
    
    # 检索到的论文片段 (Chunks)
    retrieved_chunks: Optional[List[Document]]
    
    # 引用来源 (页码、片段索引)
    citations: Optional[List[Dict[str, Any]]]
