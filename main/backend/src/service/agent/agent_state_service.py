"""
开发者: LangGraphAgent & BackendAgent
当前版本: v1.0.0
创建时间: 2026-01-14 19:00
更新时间: 2026-01-14 19:00
更新记录:
    [2026-01-14 19:00:v1.0.0:实现统一的 Agent 状态恢复服务，提供给前端和 BackendAgent 使用]
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import messages_from_dict

from base.pg.service import SessionDep
from base.pg.entity import ChatSession, AgentSession, AgentTodo
from agent.base.persistence import AgentPersistenceService
from agent.base.interrupt import InterruptManager, InterruptType, InterruptReason
from agent.base.checkpointer import get_postgres_checkpointer_context
from agent.search_agent.agent import search_agent_graph
from agent.paper_chat_agent.agent import paper_chat_agent_graph
from agent.summary_agent.agent import summary_agent_graph
from agent.mindmap_agent.agent import mindmap_agent_graph
from agent.deep_research_agent.agent import deep_research_agent_graph


class AgentStateService:
    """Agent 状态恢复服务"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.persistence_service = AgentPersistenceService(session)
        self.interrupt_manager = InterruptManager()

    # Agent 图映射
    AGENT_GRAPHS = {
        "search": search_agent_graph,
        "paper_chat": paper_chat_agent_graph,
        "summary": summary_agent_graph,
        "mindmap": mindmap_agent_graph,
        "deep_research": deep_research_agent_graph,
    }

    async def get_session_state_summary(
        self,
        user_id: UUID,
        chat_session_id: UUID
    ) -> Dict[str, Any]:
        """获取会话状态摘要"""
        # 验证会话归属
        chat_session = await self.session.get(ChatSession, chat_session_id)
        if not chat_session or chat_session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # 获取关联的 Agent 会话
        agent_sessions = await self.persistence_service.get_agent_sessions_by_chat_session(
            chat_session_id
        )

        # 构建状态摘要
        summaries = []
        for agent_session in agent_sessions:
            summary = {
                "agent_type": agent_session.agent_type,
                "status": agent_session.status,
                "created_at": agent_session.created_at.isoformat(),
                "updated_at": agent_session.updated_at.isoformat(),
            }

            # 如果有中断，添加中断信息
            if agent_session.status == "interrupted":
                interrupt_state = await self.persistence_service.get_interrupt_state(
                    agent_session.thread_id
                )
                summary["interrupt_info"] = interrupt_state

            summaries.append(summary)

        return {
            "chat_session_id": str(chat_session_id),
            "agent_sessions": summaries,
            "has_interrupted": any(s["status"] == "interrupted" for s in summaries)
        }

    async def restore_agent_session(
        self,
        user_id: UUID,
        thread_id: str,
        resume_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """恢复 Agent 会话"""
        # 获取 Agent 会话
        agent_session = await self.persistence_service.get_agent_session_by_thread(thread_id)
        if not agent_session or agent_session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Agent session not found")

        # 获取中断状态
        interrupt_state = await self.persistence_service.get_interrupt_state(thread_id)
        if not interrupt_state:
            return {"status": "no_interrupt", "can_resume": False}

        # 获取对应的 Agent 图
        agent_graph = self.AGENT_GRAPHS.get(agent_session.agent_type)
        if not agent_graph:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_session.agent_type}")

        # 使用 checkpointer 恢复状态
        async with get_postgres_checkpointer_context() as checkpointer:
            checkpoint = await checkpointer.aget(thread_id)
            if not checkpoint:
                return {"status": "checkpoint_not_found", "can_resume": False}

            # 如果有恢复数据（用户输入），处理中断恢复
            if resume_data and interrupt_state["interrupt_type"] == "strong":
                # 从中断恢复
                user_input = resume_data.get("user_input")
                if user_input is not None:
                    # 恢复状态并继续执行
                    new_state = await self.interrupt_manager.resume_from_interrupt(
                        checkpoint["state"],
                        user_input,
                        interrupt_state
                    )

                    # 更新 checkpoint
                    checkpoint["state"] = new_state
                    await checkpointer.aput(thread_id, checkpoint, {"resumed": True})

                    # 返回可继续执行的状态
                    return {
                        "status": "resumed",
                        "can_resume": True,
                        "agent_type": agent_session.agent_type,
                        "thread_id": thread_id
                    }

            # 弱中断（待办事项）
            elif interrupt_state["interrupt_type"] == "weak":
                pending_todos = interrupt_state.get("pending_todos", [])
                if pending_todos:
                    return {
                        "status": "has_todos",
                        "can_resume": True,
                        "todos": pending_todos
                    }

            # 强中断等待用户输入
            return {
                "status": "waiting_input",
                "can_resume": True,
                "interrupt_info": interrupt_state
            }

    async def complete_todo_and_resume(
        self,
        user_id: UUID,
        todo_id: UUID,
        result_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """完成待办事项并尝试恢复 Agent 执行"""
        # 获取待办事项
        todo = await self.session.get(AgentTodo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")

        # 获取关联的 Agent 会话
        agent_session = await self.session.get(AgentSession, todo.agent_session_id)
        if not agent_session or agent_session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Agent session not found")

        # 完成待办事项
        completed_todo = await self.persistence_service.complete_todo(todo_id, result_data)
        if not completed_todo:
            raise HTTPException(status_code=400, detail="Failed to complete todo")

        # 检查是否还有其他待办事项
        pending_todos = await self.persistence_service.get_pending_todos(agent_session.id)

        # 如果没有待办事项了，可以恢复 Agent 执行
        if not pending_todos:
            # 更新 Agent 会话状态
            await self.persistence_service.update_agent_session_status(
                thread_id=agent_session.thread_id,
                status="active",
                interrupt_type=None,
                interrupt_data=None
            )

            return {
                "status": "can_resume",
                "agent_type": agent_session.agent_type,
                "thread_id": agent_session.thread_id,
                "message": "All todos completed, agent can resume"
            }

        return {
            "status": "has_more_todos",
            "remaining_todos": len(pending_todos),
            "message": f"{len(pending_todos)} todos remaining"
        }

    async def get_agent_execution_history(
        self,
        user_id: UUID,
        thread_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取 Agent 执行历史"""
        # 验证会话归属
        agent_session = await self.persistence_service.get_agent_session_by_thread(thread_id)
        if not agent_session or agent_session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Agent session not found")

        # 使用 checkpointer 获取历史
        async with get_postgres_checkpointer_context() as checkpointer:
            # 获取所有 checkpoint
            checkpoints = []
            # 这里需要实现获取历史 checkpoint 的逻辑
            # 由于 LangGraph 的 checkpointer 接口限制，可能需要自定义查询

            history = []
            for checkpoint in checkpoints[-limit:]:
                history.append({
                    "timestamp": checkpoint.get("timestamp"),
                    "node": checkpoint.get("metadata", {}).get("node"),
                    "state_summary": self._summarize_state(checkpoint.get("state", {}))
                })

            return history

    def _summarize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """摘要状态信息"""
        summary = {}

        # 消息数量
        if "messages" in state:
            summary["message_count"] = len(state["messages"])
            if state["messages"]:
                summary["last_message"] = state["messages"][-1].content[:100]

        # 上下文信息
        if "context" in state:
            summary["context_count"] = len(state["context"])

        # 业务字段
        business_fields = [
            "research_topic", "found_papers", "report_content",
            "search_query", "search_results", "summary_content",
            "mindmap_data", "paper_id"
        ]

        for field in business_fields:
            if field in state and state[field] is not None:
                if isinstance(state[field], list):
                    summary[field] = f"List with {len(state[field])} items"
                elif isinstance(state[field], str):
                    summary[field] = state[field][:100] + "..." if len(state[field]) > 100 else state[field]
                else:
                    summary[field] = str(state[field])

        return summary


# FastAPI 依赖注入
async def get_agent_state_service(session: AsyncSession = Depends(SessionDep)) -> AgentStateService:
    return AgentStateService(session)
