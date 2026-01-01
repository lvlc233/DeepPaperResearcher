"""
创建时间: 2026-1-1
创建者: lxz
描述: Agent Node的案例。
"""

from schema import AgentState,AgentRutimeContext
from prompts import XX_TEMPLATE
from langchain.chat_models import init_chat_model
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage

# 如果无需外置状态
async def chat(state:AgentState,runtime:Runtime[AgentRutimeContext])->AgentState:
    """
    定义Agent的聊天节点。
    """
    # 初始化聊天模型...
    chat_model= init_chat_model() # 只是例子
    # 调用聊天模型...
    response: AIMessage = chat_model.invoke(state.messages)
    # 更新状态...
    return {
        "messages": [response],
        "context": [XX_TEMPLATE.render(question=response.content)]
    }
    
# 如果需要内置状态,使用类来包装。
class Node:
    def __init__(self,node_name:str):
        self.node_name=node_name

    async def run(self,state:AgentState,runtime:Runtime[AgentRutimeContext])->AgentState:
        """
        定义Agent的聊天节点。
        """
        # 初始化聊天模型...
        chat_model= init_chat_model() # 只是例子
        # 调用聊天模型...
        response: AIMessage = chat_model.invoke(state.messages)
        # 更新状态...
        return {
            "messages": [response],
            "context": [XX_TEMPLATE.render(question=response.content)]
        }
