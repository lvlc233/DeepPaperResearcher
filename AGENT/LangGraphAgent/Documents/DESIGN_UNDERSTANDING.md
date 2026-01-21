# Agent 系统设计理解文档

**文档信息**
- **负责人**: LangGraphAgent
- **日期**: 2026-01-07
- **关联任务**: T-009
- **状态**: Draft

---

## 1. 系统概览

本项目 `DeepPaperResearcher` 的 Agent 层旨在为科研人员提供智能化的论文搜索、阅读、总结和深度研究辅助。系统基于 **LangGraph** 框架构建，采用多 Agent 协作模式（或独立图模式），强调**图编排**、**状态管理**、**上下文工程**和**可观测性**。

核心架构约束（基于 `SPECIFICATION.md`）：
- **图编译**: 每个 Agent 是一个编译好的 `StateGraph`。
- **状态管理**: 基于 `TypedDict`，必须包含 `messages` (面向用户) 和 `context` (面向 Agent 内部)。
- **通信协议**: 使用 LangChain Messages 体系，工具调用使用 Command 更新状态。
- **异步优先**: 节点和工具均采用 `async` 实现。

---

## 2. Agent 矩阵与功能规划

根据 `后端Agent设计稿.md` 和项目需求，Agent 系统划分为以下核心模块：

### 2.1 AI 搜索 Agent (AI Search Agent)
*   **定位**: 智能信息检索专家。
*   **功能**: 
    *   基于用户 Query 进行意图分析。
    *   **混合检索**: 结合本地 RAG (向量+全文) 和 网络搜索 (Arxiv/Google)。
    *   **结果重排**: 对检索结果进行相关性评分和过滤。
*   **关键节点**:
    *   `init_node`: 加载用户画像/记忆。
    *   `rag_node`: 本地数据库检索。
    *   `web_search_node`: 网络检索。
    *   `reasoning_node`: 结果推理、排序、过滤。
    *   `storage_node`: 检索记录缓存。
*   **编排逻辑**: 并行检索 -> 聚合推理 -> 循环/结束。

### 2.2 论文总结 Agent (Paper Summarizer Agent)
*   **定位**: 单篇论文快速阅读助手。
*   **功能**: 生成论文摘要，提取关键信息。
*   **关键节点**:
    *   `context_trans_node`: 上下文转换 (OCR结果转 Markdown/结构化文本)。
    *   `reasoning_node`: LLM 总结。
    *   `persistence_node`: 结果存入数据库。
*   **编排逻辑**: 线性流: Init -> Transform -> Summarize -> Save -> End。

### 2.3 脑图生成 Agent (MindMap Agent)
*   **定位**: 结构化知识提取助手。
*   **功能**: 将论文内容转化为脑图结构 (JSON/Markdown)。
*   **关键节点**:
    *   同总结 Agent，但 `reasoning_node` 的 Prompt 和输出结构不同 (需生成层级结构)。
*   **编排逻辑**: 线性流。

### 2.4 论文内对话 Agent (In-Paper Chat Agent)
*   **定位**: 沉浸式阅读伴侣。
*   **功能**: 在特定论文上下文中回答用户问题，支持查词、解释公式、引用原文。
*   **关键节点**:
    *   `rag_node`: 针对当前论文的切片检索。
    *   `web_search_node`: (可选) 补充外部概念解释。
    *   `reasoning_node`: 答案生成与原文溯源。
*   **编排逻辑**: 对话循环 (Chat Loop)。

### 2.5 深度研究 Agent (Deep Research Agent)
*   **定位**: 自主研究员 (已部分实现)。
*   **功能**: 接受宽泛的研究课题，自主拆解任务，多轮搜索、阅读、总结，最终生成深度报告。
*   **现状**: 基于 `deepagents` 库集成，具备 Arxiv 搜索能力。需进一步增强 Plan-and-Execute 能力。

---

## 3. 关键设计模式与工程挑战

### 3.1 状态设计 (State Schema)
所有 Agent 需遵循统一的状态基类：
```python
class BaseAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages] # 用户可见历史
    context: Annotated[list[BaseMessage], add_messages]  # 内部思考流/工具结果
    # ... 其他特定字段 (如 current_paper_id, search_results 等)
```

### 3.2 上下文工程 (Context Engineering)
*   **非结构化转结构化**: PDF/OCR 结果必须经过清洗和格式化 (Markdown) 才能进入 Context。
*   **时间感知**: 所有 Context 注入必须携带时间戳。
*   **记忆注入**: 长期记忆 (Store) -> 检索 -> 压缩 -> 注入 Context。

### 3.3 工具与节点 (Tools & Nodes)
*   **Zombie Code 风险**: 避免在 Node 中写死业务逻辑，尽量封装为 Tool 供 LLM 调用，或封装为纯函数供 Node 调用。
*   **流式输出**: 必须支持 Token 级和 Event 级 (Tool Call) 的流式输出，适配前端 UI 的 `astream` 监听。

### 3.4 人工介入 (Human-in-the-loop)
*   **强介入**: 使用 `interrupt` (如确认搜索关键词、审核报告大纲)。
*   **弱介入**: 通过 Command 更新状态中的 `todo` 队列。

---

## 4. 差异分析与待办

| 模块 | 设计稿状态 | 现状 | 差距/待办 |
| :--- | :--- | :--- | :--- |
| **DeepResearch** | "交给 DeepAgent" | 初步集成 `deepagents` | 需验证其与项目基础设施 (Neo4j/PG) 的集成深度。 |
| **Search Agent** | 详细设计 | 未实现 | 需实现混合检索逻辑 (RAG + Web)。 |
| **Summarizer** | 详细设计 | 未实现 | 需实现上下文转换节点。 |
| **MindMap** | 详细设计 | 未实现 | 需设计脑图生成的 Prompt 和结构化输出 Schema。 |
| **In-Paper Chat** | 详细设计 | 未实现 | 需复用 RAG 模块。 |

## 5. 下一步计划 (Task T-010, T-011)
1.  **技术调研 (T-010)**: 确定 RAG 引擎选型 (Whoosh/ES/PGVector?), 确定 PDF 解析方案。
2.  **详细设计 (T-011)**: 定义每个 Agent 的具体 State Schema, Node Graph, 和 Tool Definitions。

