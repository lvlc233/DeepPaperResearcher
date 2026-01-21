"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14 18:00
更新时间: 2026-01-14 18:00
更新记录:
    [2026-01-14 18:00:v1.0.0:实现 Agent 持久化服务，集成 LangGraph checkpointer 和自定义持久化逻辑]
"""

from typing import Any, Optional, Dict, List
from uuid import UUID, uuid4
from datetime import datetime
import json

from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

from base.pg.entity import AgentSession, AgentTodo, ChatSession
from base.pg.service import SessionDep


class AgentPersistenceService:
    """
    Agent 持久化服务
    负责管理 Agent 会话状态、中断恢复、待办事项等
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent_session(
        self,
        user_id: UUID,
        agent_type: str,
        thread_id: str,
        chat_session_id: Optional[UUID] = None
    ) -> AgentSession:
        """创建 Agent 会话记录"""
        agent_session = AgentSession(
            user_id=user_id,
            chat_session_id=chat_session_id,
            thread_id=thread_id,
            agent_type=agent_type,
            status="active"
        )
        self.session.add(agent_session)
        await self.session.commit()
        await self.session.refresh(agent_session)
        return agent_session

    async def get_agent_session_by_thread(self, thread_id: str) -> Optional[AgentSession]:
        """通过 thread_id 获取 Agent 会话"""
        stmt = select(AgentSession).where(AgentSession.thread_id == thread_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_agent_sessions_by_chat_session(
        self,
        chat_session_id: UUID,
        limit: int = 10
    ) -> List[AgentSession]:
        """获取聊天会话关联的所有 Agent 会话"""
        stmt = select(AgentSession).where(
            AgentSession.chat_session_id == chat_session_id
        ).order_by(desc(AgentSession.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_agent_session_status(
        self,
        thread_id: str,
        status: str,
        interrupt_type: Optional[str] = None,
        interrupt_data: Optional[Dict] = None
    ) -> Optional[AgentSession]:
        """更新 Agent 会话状态"""
        agent_session = await self.get_agent_session_by_thread(thread_id)
        if not agent_session:
            return None

        agent_session.status = status
        agent_session.interrupt_type = interrupt_type
        agent_session.interrupt_data = interrupt_data
        agent_session.updated_at = datetime.utcnow()

        if status == "completed":
            agent_session.completed_at = datetime.utcnow()

        self.session.add(agent_session)
        await self.session.commit()
        await self.session.refresh(agent_session)
        return agent_session

    async def create_todo(
        self,
        agent_session_id: UUID,
        todo_type: str,
        todo_data: Dict[str, Any]
    ) -> AgentTodo:
        """创建待办事项（弱人工介入）"""
        todo = AgentTodo(
            agent_session_id=agent_session_id,
            todo_type=todo_type,
            todo_data=todo_data,
            status="pending"
        )
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def get_pending_todos(self, agent_session_id: UUID) -> List[AgentTodo]:
        """获取待处理的待办事项"""
        stmt = select(AgentTodo).where(
            AgentTodo.agent_session_id == agent_session_id,
            AgentTodo.status == "pending"
        ).order_by(AgentTodo.created_at)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def complete_todo(
        self,
        todo_id: UUID,
        result_data: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentTodo]:
        """完成待办事项"""
        stmt = select(AgentTodo).where(AgentTodo.id == todo_id)
        result = await self.session.execute(stmt)
        todo = result.scalar_one_or_none()

        if not todo:
            return None

        todo.status = "completed"
        todo.completed_at = datetime.utcnow()

        # 更新待办数据中的结果
        if result_data:
            todo_data = dict(todo.todo_data) if todo.todo_data else {}
            todo_data["result"] = result_data
            todo.todo_data = todo_data

        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def get_interrupt_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取中断状态信息"""
        agent_session = await self.get_agent_session_by_thread(thread_id)
        if not agent_session or agent_session.status != "interrupted":
            return None

        return {
            "interrupt_type": agent_session.interrupt_type,
            "interrupt_data": agent_session.interrupt_data,
            "pending_todos": [
                {
                    "id": str(todo.id),
                    "type": todo.todo_type,
                    "data": todo.todo_data
                }
                for todo in await self.get_pending_todos(agent_session.id)
            ]
        }


class EnhancedCheckpointSaver:
    """
    增强的 Checkpoint 保存器
    集成 LangGraph checkpointer 和自定义持久化逻辑
    """

    def __init__(
        self,
        checkpointer: BaseCheckpointSaver,
        persistence_service: AgentPersistenceService
    ):
        self.checkpointer = checkpointer
        self.persistence_service = persistence_service

    async def asave_checkpoint(
        self,
        thread_id: str,
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> None:
        """保存 checkpoint 并更新 Agent 会话状态"""
        # 保存到 LangGraph checkpoint
        await self.checkpointer.aput(thread_id, checkpoint, metadata)

        # 检查是否有中断
        if metadata.get("interrupt"):
            interrupt_data = metadata.get("interrupt_data", {})
            interrupt_type = interrupt_data.get("type", "strong")

            # 更新 Agent 会话状态
            await self.persistence_service.update_agent_session_status(
                thread_id=thread_id,
                status="interrupted",
                interrupt_type=interrupt_type,
                interrupt_data=interrupt_data
            )

            # 如果是弱中断，创建待办事项
            if interrupt_type == "weak":
                agent_session = await self.persistence_service.get_agent_session_by_thread(thread_id)
                if agent_session:
                    await self.persistence_service.create_todo(
                        agent_session_id=agent_session.id,
                        todo_type=interrupt_data.get("todo_type", "approval"),
                        todo_data=interrupt_data.get("todo_data", {})
                    )

    async def arestore_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """恢复 checkpoint"""
        # 从 LangGraph checkpoint 获取
        checkpoint = await self.checkpointer.aget(thread_id)
        if not checkpoint:
            return None

        # 更新 Agent 会话状态为 active
        await self.persistence_service.update_agent_session_status(
            thread_id=thread_id,
            status="active",
            interrupt_type=None,
            interrupt_data=None
        )

        return checkpoint

    # 代理其他方法到原始 checkpointer
    def __getattr__(self, name):
        return getattr(self.checkpointer, name)