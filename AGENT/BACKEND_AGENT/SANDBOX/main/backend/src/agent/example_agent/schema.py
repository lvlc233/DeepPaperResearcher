"""
创建时间: 2026-1-1
创建者: lxz
描述: Agent相关的数据结构的定义:案例
"""
from langgraph.graph.message import BaseMessage,add_messages
from typing import Annotated, TypedDict

class AgentState(TypedDict):
    """
    定义Agent的状态
    """
    # 定义messages字段，用于存储面向交互者(用户)的历史记录消息
    messages: Annotated[list[BaseMessage], add_messages]
    # 定义Agent内部使用的短期上下文信息
    # 在对Agent的行为有影响的节点和工具中都需要更新上下文数据
    # 并在模型调用处结合其他信息合成最终的Agent上下文
    context: Annotated[list[BaseMessage] , add_messages]

    # 其他....

class AgentRutimeContext(TypedDict):
    """
    定义Agent的静态资源信息。
    """
    # 定义Agent运行时候的会话id
    # 用于持久化Agent的运行状态和数据回复。
    session_id:str

"""
    结构化输出
"""
class AgentOutputStruct(TypedDict):
    """
        定义Agent的输出结构。
    """
    # 定义Agent的回复消息
    reply: Annotated[str, ..., "Agent的回复消息..."]
