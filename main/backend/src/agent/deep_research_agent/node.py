"""
创建时间: 2026-01-02
创建者: LangGraphAgent
描述: DeepResearchAgent 的核心节点实现。
"""
import logging
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from .schema import DeepResearchState
from .prompts import DEEP_RESEARCH_SYSTEM_PROMPT # 复用 System Prompt
from ..common.tools import read_paper, internet_search

logger = logging.getLogger(__name__)

def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)

async def plan_node(state: DeepResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    规划阶段：分析主题，生成子主题。
    """
    messages = state["messages"]
    last_msg = messages[-1]
    topic = last_msg.content
    
    # 简单的逻辑：如果 state 中已有 topic，则复用，否则从消息中提取
    # 这里简化处理，直接使用用户消息作为 topic
    
    logger.info(f"Planning research for topic: {topic}")
    
    # 模拟规划逻辑 (实际可调用 LLM)
    sub_topics = [
        f"{topic} 的最新进展",
        f"{topic} 的关键挑战",
        f"{topic} 的未来趋势"
    ]
    
    return {
        "research_topic": topic,
        "sub_topics": sub_topics,
        "messages": [AIMessage(content=f"已生成研究计划，包含 {len(sub_topics)} 个子方向。")]
    }

async def research_node(state: DeepResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    研究阶段：针对每个子主题进行搜索和摘要。
    """
    sub_topics = state.get("sub_topics", [])
    found_papers = []
    
    for sub in sub_topics:
        # 模拟搜索
        try:
            # 真实场景应调用 search 工具
            # search_res = await internet_search.ainvoke(sub)
            # 这里简化，直接 mock 结果
            logger.info(f"Researching sub-topic: {sub}")
            
            paper = {
                "title": f"Paper about {sub}",
                "url": "http://arxiv.org/abs/mock",
                "summary": f"This is a summary for {sub}",
                "relevance_score": 0.9
            }
            found_papers.append(paper)
            
        except Exception as e:
            logger.error(f"Error researching {sub}: {e}")
            
    return {
        "found_papers": found_papers,
        "messages": [AIMessage(content=f"已完成搜索，找到 {len(found_papers)} 篇相关论文。")]
    }

async def report_node(state: DeepResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    报告阶段：汇总信息，生成报告。
    """
    topic = state.get("research_topic", "Unknown Topic")
    papers = state.get("found_papers", [])
    
    findings = "\n".join([f"- {p['title']}: {p['summary']}" for p in papers])
    
    report = f"""
# 研究报告: {topic}

## 综述
本报告基于自动化的深度研究生成。

## 研究发现
{findings}

## 结论
该领域目前处于快速发展阶段，具有广阔的应用前景。
"""
    
    return {
        "report_content": report,
        "messages": [AIMessage(content=report)],
        "sender": "DeepResearchAgent"
    }

