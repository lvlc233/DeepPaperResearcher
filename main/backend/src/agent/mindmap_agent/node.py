"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:实现 MindMapAgent 核心节点]
"""

import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from .schema import MindMapAgentState
from .prompts import mindmap_generator_prompt
from ..common.tools import read_paper

logger = logging.getLogger(__name__)

def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)

async def load_paper_node(state: MindMapAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    加载论文内容 (复用逻辑)。
    """
    paper_id = state.get("paper_id")
    if not paper_id:
        return {}
        
    # 模拟构建 URL
    if paper_id.startswith("http"):
        url = paper_id
    else:
        url = f"http://arxiv.org/abs/{paper_id}"
        
    try:
        content = await read_paper.ainvoke(url)
    except Exception as e:
        logger.error(f"Failed to load paper: {e}")
        content = f"Error loading paper: {str(e)}"
        
    return {"paper_content": content}

async def generate_mindmap_node(state: MindMapAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    生成 Mermaid 脑图。
    """
    paper_content = state.get("paper_content")
    depth = state.get("depth", 2)
    
    if not paper_content:
        return {
            "mindmap_data": "mindmap\n  root((Error))\n    No Content",
            "messages": [AIMessage(content="无法获取论文内容。")]
        }
        
    llm = get_llm()
    chain = mindmap_generator_prompt | llm
    
    # 截断以适应 Context
    safe_content = paper_content[:15000]
    
    response = await chain.ainvoke({
        "paper_content": safe_content,
        "depth": depth
    }, config=config)
    
    mindmap_code = response.content.strip()
    # 清理可能存在的 markdown code block 标记
    mindmap_code = mindmap_code.replace("```mermaid", "").replace("```", "").strip()
    
    return {
        "mindmap_data": mindmap_code,
        "messages": [response],
        "sender": "MindMapAgent"
    }
