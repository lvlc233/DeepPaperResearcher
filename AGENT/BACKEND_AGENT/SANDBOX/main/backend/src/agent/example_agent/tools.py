"""
创建时间: 2026-1-1
创建者: lxz
描述: Agent工具的定义:案例
"""

from langchain.agents import tool
from prompts import XX_DESCRIPTION

@tool("simpale_tool",description=XX_DESCRIPTION)
async def simpale_tool(id:str,query:str):
     # 这里的信息就是给开发者看的了。
     """
        创建时间: 2026-1-1
        创建者: lxz
        描述: 一个简单的工具，用于返回查询的结果
     """
     return f"工具{id}的结果是:{query}"