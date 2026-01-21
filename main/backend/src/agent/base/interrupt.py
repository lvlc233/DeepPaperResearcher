"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14 18:30
更新时间: 2026-01-14 18:30
更新记录:
    [2026-01-14 18:30:v1.0.0:实现 Agent 中断恢复机制，支持强人工介入和状态恢复]
"""

from typing import Any, Dict, Optional, TypedDict
from abc import ABC, abstractmethod
from enum import Enum

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command

# TODO:看着还不错,晚点再审核,看看怎么使用的
class InterruptType(Enum):
    """中断类型枚举"""
    STRONG = "strong"  # 强中断 - 需要用户明确干预
    WEAK = "weak"     # 弱中断 - 通过待办事项处理


class InterruptReason(Enum):
    """中断原因枚举"""
    NEED_APPROVAL = "need_approval"  # 需要用户审批
    NEED_INPUT = "need_input"       # 需要用户输入
    NEED_SELECTION = "need_selection"  # 需要用户选择
    NEED_CONFIRMATION = "need_confirmation"  # 需要用户确认
    TOOL_ERROR = "tool_error"       # 工具执行错误
    RATE_LIMIT = "rate_limit"       # 速率限制


class InterruptData(TypedDict, total=False):
    """中断数据结构"""
    type: str  # interrupt 类型
    reason: str  # 中断原因
    message: str  # 给用户的消息
    payload: Dict[str, Any]  # 额外数据
    options: Optional[list]  # 选项列表（选择型中断）
    timeout: Optional[int]  # 超时时间（秒）


class BaseInterruptHandler(ABC):
    """中断处理器基类"""

    @abstractmethod
    async def handle_interrupt(self, state: Dict[str, Any], interrupt_data: InterruptData) -> Any:
        """处理中断请求"""
        pass

    @abstractmethod
    async def resume_from_interrupt(self, state: Dict[str, Any], user_input: Any) -> Dict[str, Any]:
        """从中断恢复"""
        pass


class ApprovalInterruptHandler(BaseInterruptHandler):
    """审批中断处理器"""

    async def handle_interrupt(self, state: Dict[str, Any], interrupt_data: InterruptData) -> bool:
        """处理审批中断"""
        # 构建审批消息
        message = interrupt_data.get("message", "需要您的审批确认")
        payload = interrupt_data.get("payload", {})

        # 使用 LangGraph 的 interrupt 功能
        result = interrupt({
            "type": InterruptType.STRONG.value,
            "reason": InterruptReason.NEED_APPROVAL.value,
            "message": message,
            "payload": payload,
            "action": "approve_or_reject"
        })

        return result

    async def resume_from_interrupt(self, state: Dict[str, Any], user_input: bool) -> Dict[str, Any]:
        """从审批中断恢复"""
        # 更新状态
        if user_input:
            state["last_action_approved"] = True
            state["context"] = state.get("context", []) + [
                AIMessage(content="用户已批准该操作")
            ]
        else:
            state["last_action_approved"] = False
            state["context"] = state.get("context", []) + [
                AIMessage(content="用户已拒绝该操作")
            ]

        return state


class InputInterruptHandler(BaseInterruptHandler):
    """输入中断处理器"""

    async def handle_interrupt(self, state: Dict[str, Any], interrupt_data: InterruptData) -> str:
        """处理输入中断"""
        message = interrupt_data.get("message", "需要您的输入")
        placeholder = interrupt_data.get("payload", {}).get("placeholder", "")

        result = interrupt({
            "type": InterruptType.STRONG.value,
            "reason": InterruptReason.NEED_INPUT.value,
            "message": message,
            "placeholder": placeholder
        })

        return result

    async def resume_from_interrupt(self, state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """从输入中断恢复"""
        state["user_input"] = user_input
        state["context"] = state.get("context", []) + [
            HumanMessage(content=user_input)
        ]
        return state


class SelectionInterruptHandler(BaseInterruptHandler):
    """选择中断处理器"""

    async def handle_interrupt(self, state: Dict[str, Any], interrupt_data: InterruptData) -> int:
        """处理选择中断"""
        message = interrupt_data.get("message", "请选择一个选项")
        options = interrupt_data.get("options", [])

        result = interrupt({
            "type": InterruptType.STRONG.value,
            "reason": InterruptReason.NEED_SELECTION.value,
            "message": message,
            "options": options
        })

        return result

    async def resume_from_interrupt(self, state: Dict[str, Any], user_input: int) -> Dict[str, Any]:
        """从选择中断恢复"""
        state["selected_option"] = user_input
        state["context"] = state.get("context", []) + [
            HumanMessage(content=f"用户选择了选项 {user_input}")
        ]
        return state


class InterruptManager:
    """中断管理器"""

    def __init__(self):
        self.handlers = {
            InterruptReason.NEED_APPROVAL: ApprovalInterruptHandler(),
            InterruptReason.NEED_INPUT: InputInterruptHandler(),
            InterruptReason.NEED_SELECTION: SelectionInterruptHandler(),
        }

    def get_handler(self, reason: str) -> Optional[BaseInterruptHandler]:
        """获取中断处理器"""
        try:
            enum_reason = InterruptReason(reason)
            return self.handlers.get(enum_reason)
        except ValueError:
            return None

    async def create_strong_interrupt(
        self,
        state: Dict[str, Any],
        reason: InterruptReason,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[list] = None
    ) -> Command:
        """创建强中断"""
        handler = self.get_handler(reason)
        if not handler:
            raise ValueError(f"No handler for interrupt reason: {reason}")

        interrupt_data = InterruptData(
            type=InterruptType.STRONG.value,
            reason=reason.value,
            message=message,
            payload=payload or {},
            options=options
        )

        # 保存中断信息到状态
        state["interrupt_info"] = interrupt_data

        # 创建中断命令
        return Command(
            update={"interrupt_info": interrupt_data},
            goto="__interrupt__"
        )

    async def create_weak_interrupt(
        self,
        state: Dict[str, Any],
        reason: InterruptReason,
        message: str,
        todo_type: str,
        todo_data: Dict[str, Any]
    ) -> Command:
        """创建弱中断（待办事项）"""
        interrupt_data = InterruptData(
            type=InterruptType.WEAK.value,
            reason=reason.value,
            message=message,
            payload={
                "todo_type": todo_type,
                "todo_data": todo_data
            }
        )

        # 保存中断信息到状态
        state["interrupt_info"] = interrupt_data

        # 返回继续执行的命令
        return Command(
            update={
                "interrupt_info": interrupt_data,
                "pending_todos": state.get("pending_todos", []) + [{
                    "type": todo_type,
                    "data": todo_data,
                    "message": message
                }]
            },
            goto=None  # 继续执行
        )

    async def resume_from_interrupt(
        self,
        state: Dict[str, Any],
        user_input: Any,
        interrupt_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从中断恢复"""
        if not interrupt_info:
            interrupt_info = state.get("interrupt_info")

        if not interrupt_info:
            return state

        reason = InterruptReason(interrupt_info["reason"])
        handler = self.get_handler(reason)

        if not handler:
            return state

        # 使用处理器恢复状态
        new_state = await handler.resume_from_interrupt(state, user_input)

        # 清除中断信息
        new_state["interrupt_info"] = None

        return new_state


# 全局中断管理器实例
interrupt_manager = InterruptManager()