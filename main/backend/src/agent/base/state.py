"""
开发者: LangGraphAgent
当前版本: v2.0.0
创建时间: 2026-01-08 18:05
更新时间: 2026-01-14 20:00
更新记录:
    [2026-01-08 18:05:v1.0.0:定义 BaseAgentState 基类,包含 messages, context, sender 字段,用于所有 Agent 的状态管理]
    [2026-01-14 20:00:v2.0.0:添加持久化相关字段，支持中断恢复和待办事项]
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class BaseAgentState(TypedDict):
    """
    Agent 系统的基础状态定义。
    所有具体的 Agent 状态都应该继承自此基类。
    """

    # 面向用户的历史消息记录。
    # 使用 add_messages reducer，支持增量更新。
    # 任何情况下 Agent 的上下文不应该直接使用 messages 中的任意数据，除非它经过处理或在其他字段中存储。
    messages: Annotated[List[BaseMessage], add_messages]

    # 面向 Agent 的内部上下文信息 (如检索到的文档、中间思考过程、工具调用结果等)。
    # 这些信息通常对用户不可见，但对 Agent 的推理至关重要。
    # 同样使用 add_messages reducer 以支持增量累积。
    context: Annotated[List[BaseMessage], add_messages]

    # 标识当前最后发言的 Agent 名称。
    # 用于多 Agent 协作时的路由判断。
    sender: Optional[str]

    # ===== 持久化相关字段 =====

    # 中断信息（当 Agent 被中断时填充）
    interrupt_info: Optional[Dict[str, Any]]

    # 待办事项列表（弱人工介入）
    pending_todos: Annotated[List[Dict[str, Any]], lambda x, y: x + y]

    # 已完成的待办事项
    completed_todos: Annotated[List[Dict[str, Any]], lambda x, y: x + y]

    # 用户输入（用于从中断恢复）
    user_input: Optional[Any]

    # 最后操作是否被批准（审批中断用）
    last_action_approved: Optional[bool]

    # 用户选择的选项（选择中断用）
    selected_option: Optional[int]

    # 执行历史（可选，用于调试和审计）
    execution_history: Annotated[List[Dict[str, Any]], lambda x, y: x + y]

    # 错误信息（当发生错误时）
    error_info: Optional[Dict[str, Any]]


class PersistenceConfig(TypedDict):
    """
    持久化配置
    """
    # 是否启用持久化
    enable_persistence: bool

    # 线程ID（用于checkpointer）
    thread_id: Optional[str]

    # 用户ID
    user_id: Optional[str]

    # 会话ID
    session_id: Optional[str]

    # 最大检查点数量
    max_checkpoints: int

    # 是否启用中断
    enable_interrupts: bool