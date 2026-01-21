# LangGraph Agent 任务清单

本文档详细追踪 LangGraph Agent 的开发任务，对应主任务 T-019 和 T-020。

## 任务概览

| 任务 ID | 对应主任务 | 任务名称 | 优先级 | 状态 | 负责人 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| LG-001 | T-019 | 定义 BaseAgentState | P0 | 🟢 | LangGraphAgent |
| LG-002 | T-019 | 实现 Checkpointer (MemorySaver) | P0 | 🟢 | LangGraphAgent |
| LG-003 | T-019 | 封装基础 Tools (Search, Retriever) | P1 | 🟡 | LangGraphAgent |
| LG-004 | T-020 | 实现 SearchAgent 图编排 | P1 | 🟢 | LangGraphAgent |
| LG-005 | T-020 | 实现 InPaperChatAgent 图编排 | P1 | 🟢 | LangGraphAgent |
| LG-006 | T-020 | 集成 SSE 流式输出 | P1 | 🔴 | LangGraphAgent |

## 任务详情

### LG-001: 定义 BaseAgentState
- **目标**: 建立所有 Agent 共享的状态基类。
- **要求**:
  - 继承自 `TypedDict`。
  - 包含 `messages` (Annotated[list[BaseMessage], add_messages])。
  - 包含 `context` (用于存放检索到的文档、中间思考过程)。
  - 包含 `sender` (标识当前最后发言的 Agent)。
- **产出**: `backend/src/agent/base/state.py`

### LG-002: 实现 Checkpointer
- **目标**: 实现基于 Postgres 的持久化存储，支持长对话记忆。
- **要求**:
  - 使用 `langgraph.checkpoint.postgres` 或自定义实现。
  - 确保存储是异步的。
  - 需要序列化/反序列化支持。
- **产出**: `backend/src/agent/base/checkpointer.py` (或直接配置)

### LG-003: 封装基础 Tools
- **目标**: 将 Service 层功能封装为 LangChain Tools。
- **要求**:
  - `search_local_papers`: 基于 pgvector 检索本地论文库。
  - `fetch_arxiv`: 搜索 Arxiv 论文。
  - 工具需包含详细的 docstring 和 args_schema。
- **产出**: `backend/src/agent/common/tools.py`

### LG-004: 实现 SearchAgent 图编排
- **目标**: 实现 AI 搜索助手。
- **流程**:
  1. `analyze_query`: 分析用户意图。
  2. `retrieve`: 并行调用本地和网络搜索。
  3. `rank`: 对结果进行重排。
  4. `synthesize`: 生成回答。
- **产出**: `backend/src/agent/search_agent/graph.py`

### LG-005: 实现 InPaperChatAgent 图编排
- **目标**: 实现单篇论文问答助手。
- **流程**:
  1. 接收 `paper_id` 和 `query`。
  2. 检索该论文的 Chunks。
  3. 生成回答并标注引用。
- **产出**: `backend/src/agent/paper_chat_agent/graph.py`

### LG-006: 集成 SSE 流式输出
- **目标**: 适配前端的流式显示需求。
- **要求**:
  - 支持 token 级流式输出。
  - 支持 tool_call 状态流式输出。
  - 格式符合 Vercel AI SDK 或自定义 SSE 协议。
