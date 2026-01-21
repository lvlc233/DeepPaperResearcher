"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:定义 MindMapAgentState]
"""

from typing import Optional, List, Dict, Any
from ..base.state import BaseAgentState

class MindMapAgentState(BaseAgentState):
    """
    MindMapAgent (脑图生成助手) 的状态定义。
    """
    
    # 目标论文 ID (输入)
    paper_id: str
    
    # 论文全文内容 (中间状态)
    paper_content: Optional[str]
    
    # 生成的脑图数据 (输出)
    # 格式可以是 Mermaid Markdown, JSON, 或其他前端可渲染格式
    mindmap_data: Optional[str] 
    
    # 脑图层级深度 (配置)
    depth: int = 2
