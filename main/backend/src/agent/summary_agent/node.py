"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:实现 SummaryAgent 核心节点: load_paper, generate_summary]
"""

import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from .schema import SummaryAgentState
from .prompts import summary_generator_prompt
# 复用已有的 read_paper 工具 (或者未来直接调 Service)
from ..common.tools import read_paper 

logger = logging.getLogger(__name__)

def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)

# TODO: 用现有的service,然后,流程是这样子的,1.首先要保证这个论文已经上传并解析成功
async def load_paper_node(state: SummaryAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    加载论文内容。
    """
    paper_id = state.get("paper_id")
    if not paper_id:
        raise ValueError("Paper ID is required for SummaryAgent.")
    
    # 模拟构建 URL (实际应由 Service 处理 ID -> Content 的映射)
    # 这里为了演示复用 read_paper 工具，假设 ID 能转为 URL，或者工具支持 ID
    # 临时逻辑: 假设 paper_id 是 URL，或者拼接 Arxiv URL
    if paper_id.startswith("http"):
        url = paper_id
    else:
        # 假设是 Arxiv ID
        url = f"http://arxiv.org/abs/{paper_id}"
        
    logger.info(f"Loading paper from: {url}")
    
    # 调用工具获取内容
    try:
        content = await read_paper.ainvoke(url)
    except Exception as e:
        logger.error(f"Failed to load paper: {e}")
        content = f"Error loading paper: {str(e)}"
        
    return {
        "paper_content": content
    }

async def generate_summary_node(state: SummaryAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    生成总结。
    """
    paper_content = state.get("paper_content")
    language = state.get("language", "Chinese")
    
    if not paper_content:
        return {
            "summary": "无法获取论文内容，无法生成总结。",
            "messages": [AIMessage(content="无法获取论文内容，无法生成总结。")]
        }
        
    llm = get_llm()
    chain = summary_generator_prompt | llm
    
    
    response = await chain.ainvoke({
        "paper_content": paper_content,
        "language": language
    }, config=config)
    
    return {
        "summary": response.content,
        "messages": [response], # 将总结作为 AI 回复推入消息历史
        "sender": "SummaryAgent"
    }
