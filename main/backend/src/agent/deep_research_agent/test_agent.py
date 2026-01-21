"""
创建时间: 2026-01-02
创建者: LangGraphAgent
描述: DeepResearchAgent 的集成测试脚本。
"""
import asyncio
import sys
import os

from langchain_core.messages import HumanMessage
# 确保在运行模块时可以找到包
from agent.deep_research_agent.agent import deep_research_agent

async def main():
    print("开始 DeepResearchAgent 测试...")
    
    initial_state = {
        "messages": [HumanMessage(content="我想研究 2024 年的 Agent 技术")]
    }
    
    try:
        async for event in deep_research_agent.astream(initial_state):
            for key, value in event.items():
                print(f"节点: {key}")
                if value:
                    try:
                        # 尝试像字典一样访问
                        if hasattr(value, "items") or isinstance(value, dict):
                             if "messages" in value:
                                msgs = value["messages"]
                                if isinstance(msgs, list) and msgs:
                                    last_msg = msgs[-1]
                                    if hasattr(last_msg, "content"):
                                        print(f"内容: {last_msg.content[:100]}...")
                        else:
                            # 可能是 Overwrite 对象或其他
                            print(f"收到值更新 (类型: {type(value).__name__})")
                    except Exception as inner_e:
                        print(f"无法解析值: {inner_e}")
    except Exception as e:
        print(f"执行期间出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
