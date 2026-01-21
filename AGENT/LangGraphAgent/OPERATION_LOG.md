
# 操作日志 - LangGraphAgent

## 2026-01-08 18:55
**行动**: 实现了 SearchAgent (LG-004) 和 InPaperChatAgent (LG-005)。

**详细信息**:
1. **SearchAgent (LG-004)**
    - 定义了继承自 `BaseAgentState` 的 `SearchAgentState`。
    - 实现了节点：`analyze_query`、`retrieve`、`generate`。
    - 创建了编译后的图 `search_agent_graph`。
    - 修复了 `node.py`，使用 `get_llm()` 工厂函数，避免了导入时的全局副作用。

2. **InPaperChatAgent (LG-005)**
    - 定义了支持 `paper_id` 的 `InPaperChatState`。
    - 实现了节点：`retrieve_paper_chunks`、`generate_answer`。
    - 创建了编译后的图 `paper_chat_agent_graph`。

3. **基础设施**
    - 通过 `uv add` 安装了 `langchain_openai`。
    - 验证了两个 Agent 的导入和图编译。

**验证**:
- `python -c "from src.agent.search_agent import search_agent_graph..."` (成功)
- `python -c "from src.agent.paper_chat_agent import paper_chat_agent_graph..."` (成功)

**下一步**:
- LG-006：集成 SSE 流式传输。
- 一旦可用，用实际的服务调用替换模拟工具。

## 2026-01-14 16:30
**行动**: 建立了测试框架并优化了 DeepResearchAgent 工具（LG-Test-001）。

**详细信息**:
1. **测试框架 (test/agent/)**
    - 创建了带有 `anyio` 后端配置的 `conftest.py`。
    - 实现了 `test_deep_research_agent.py`：完整覆盖 `internet_search`、`read_paper`、`plan_research` 和 `generate_report`。
    - 实现了 `test_search_agent.py` 和 `test_paper_chat_agent.py`：验证图编译和状态初始化。
    - **结果**：8/8 个测试通过。

2. **代码优化 (DeepResearchAgent)**
    - 将 `node.py` 中的 `plan_research` 和 `generate_report` 重构为**异步**工具。
    - 这与 `MEMORY.md` 的异步规范一致，并防止事件循环阻塞。

3. **验证**
    - `pytest test/agent/` 执行成功。

## 2026-01-14 22:00
**行动**: 完成了 Agent 持久化机制的设计调研和文档整理（LG-Persistence-Design）。

**详细信息**:
1. **文档调研**
   - 使用 mcp__langgraph-docs__SearchDocsByLangChain 工具查询了 LangGraph checkpoint 机制
   - 深入理解了以下核心概念：
     - Checkpoint 机制：在每个超级步骤保存图状态快照
     - 不同 Saver 实现：InMemorySaver、SqliteSaver、PostgresSaver、AsyncPostgresSaver
     - 异步状态保存：AsyncPostgresSaver 的使用方法和最佳实践
     - 序列化配置：JsonPlusSerializer、pickle_fallback、EncryptedSerializer
     - 人工介入恢复：interrupt() 函数和 Command(resume=...) 的使用
     - 生命周期管理：TTL 配置和清理策略

2. **代码审查**
   - 审查了现有持久化实现：`AgentPersistenceService` 和 `EnhancedCheckpointSaver`
   - 确认了数据库实体设计：`AgentSession`、`AgentTodo`、`AgentCheckpoint`
   - 验证了 checkpointer 工厂方法已支持 AsyncPostgresSaver

3. **架构理解**
   - 项目采用双轨存储：LangGraph checkpointer + 自定义持久化
   - 支持强中断（interrupt）和弱中断（todo）两种模式
   - 前端通过 SSE 事件处理中断和待办事项

**下一步**:
- LG-006：集成 SSE 流式传输。
- 实现具体 Agent 的中断逻辑和测试验证

## 2026-01-14 16:50
**行动**: 实现了搜索增强 Agent 和摘要 Agent（T-122 ~ T-129）。

**详细信息**:
1. **搜索增强 Agent（优化）**
    - 验证了 `SearchAgent` 架构符合"增强"要求（分析 -> 检索 -> 生成）。
    - 在 `test_search_agent.py` 中使用 `RunnableLambda` 模拟完成了完整的图执行测试。
    - 验证了数据流：`search_query` 优化 -> `search_results` 检索 -> `messages` 生成。

2. **摘要 Agent（新实现）**
    - 初始化了 `src/agent/summary_agent/` 模块。
    - 定义了 `SummaryAgentState`：支持 `paper_id`、`paper_content`、`summary`、`language`。
    - 实现了节点：
        - `load_paper_node`：通过 `read_paper` 工具获取论文内容（已移动到公共工具）。
        - `generate_summary_node`：使用 LLM 生成结构化摘要。
    - 编译图：线性流程 `load_paper` -> `generate_summary`。
    - 实现测试：`test_summary_agent.py` 验证编译和执行流程。

3. **基础设施**
    - 将 `read_paper` 工具移动到 `src/agent/common/tools.py` 以供复用。
    - 使用 `RunnableLambda` 标准化了 LangGraph 中模拟 LLM 的测试模式。

**验证**:
- `pytest test/agent/test_search_agent.py test/agent/test_summary_agent.py` 通过（5/5 个测试）。

**下一步**:
- 实现阅读模块的对话 Agent（T-130 ~ T-133）。
- 实现思维导图生成 Agent（T-134 ~ T-137）。

## 2026-01-14 17:15
**行动**: 实现了阅读模块对话 Agent 和脑图生成 Agent（T-130 ~ T-137）。

**详细信息**:
1. **阅读模块对话 Agent (InPaperChatAgent)**
    - **状态 (T-130)**: 确认 `InPaperChatState` 支持 `paper_id` 和 `retrieved_chunks`。
    - **节点 (T-131)**: 增强了 `retrieve_paper_chunks_node`，添加了测试模式支持 (`is_test`)，允许在无真实数据库连接时返回 Mock 数据。
    - **测试 (T-133)**: 完善了 `test_paper_chat_agent.py`，使用 `RunnableLambda` 模拟 LLM，并通过 `is_test` 配置验证了完整的 RAG 流程。

2. **脑图生成 Agent (MindMapAgent)**
    - **初始化**: 创建了 `src/agent/mindmap_agent/` 模块。
    - **状态 (T-134)**: 定义了 `MindMapAgentState`，包含 `paper_id`, `paper_content`, `mindmap_data`, `depth`。
    - **节点 (T-135)**:
        - `load_paper_node`: 复用 `read_paper` 工具。
        - `generate_mindmap_node`: 实现从文本到 Mermaid Mindmap 格式的转换逻辑，包含 Markdown 清理。
    - **图与测试 (T-136, T-137)**: 构建了线性执行图，并通过 `test_mindmap_agent.py` 验证了从加载到生成的流程。

**验证**:
- `pytest test/agent/` 全量执行通过（10/10 个测试），覆盖 Search, Summary, Chat, MindMap 四大 Agent。

**下一步**:
- T-138: 深度搜索 Agent 重构。
- T-142: 状态持久化实现。

## 2026-01-14 17:52
**行动**: 重构 DeepResearchAgent 并实现统一状态持久化 (T-138 ~ T-144)。

**详细信息**:
1. **DeepResearchAgent 重构 (T-138 ~ T-141)**
    - **重构 (T-138)**: 移除了 `deepagents` 黑盒依赖，转为显式的 `StateGraph` 实现。
    - **状态与节点**: 完善了 `DeepResearchState`，实现了 `plan_node`, `research_node`, `report_node`。
    - **工具复用**: 将 `internet_search` 和 `read_paper` 移动到 `common/tools.py` 供全局复用。
    - **测试 (T-141)**: 更新了 `test_deep_research_agent.py`，验证了多轮迭代逻辑和状态更新。

2. **状态持久化 (T-142 ~ T-144)**
    - **实现 (T-142, T-143)**: 在 `checkpointer.py` 中集成了 `AsyncPostgresSaver`。
        - 使用 `AsyncConnectionPool` 管理数据库连接。
        - 实现了 `get_postgres_checkpointer_context` 上下文管理器，支持从 `settings` 自动加载配置。
        - 增加了对 `ImportError` 的优雅降级处理。
    - **测试 (T-144)**: 创建了 `test_persistence.py`。
        - 验证了 `MemorySaver` 的基础功能。
        - 通过 `unittest.mock` 模拟了 Postgres 连接池和 Saver，验证了初始化逻辑和图的集成。
        - 修复了相对导入路径问题，确保配置正确加载。

**验证**:
- `pytest main/backend/test/agent/test_persistence.py` 通过。
- 所有 Agent 的单元测试均通过。

**下一步**:
- 进行整体集成测试。
- 准备部署与 API 接入。
