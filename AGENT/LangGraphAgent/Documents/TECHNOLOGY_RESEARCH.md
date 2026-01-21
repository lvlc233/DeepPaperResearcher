# Agent 技术选型与实现细节调研文档

**文档信息**
- **负责人**: LangGraphAgent
- **日期**: 2026-01-07
- **关联任务**: T-010
- **状态**: Review Needed

---

## 1. 核心技术决策摘要

| 模块 | 选型方案 | 替代方案 (已否决) | 决策理由 |
| :--- | :--- | :--- | :--- |
| **RAG 引擎** | **PostgreSQL (pgvector + Full-Text Search)** | Whoosh, Elasticsearch, Neo4j (仅做检索) | **架构极简**。利用 PG 同时实现语义搜索 (Vector) 和关键词搜索 (BM25)，通过 RRF 算法融合，无需引入额外的检索引擎维护成本。 |
| **PDF 解析** | **Marker** | PyMuPDF, pdfplumber, Unstructured | **学术优化**。Marker 专为 PDF 转 Markdown 设计，对公式 (LaTeX) 和表格的处理能力远优于通用工具，适合论文场景。 |
| **Agent 编排** | **LangGraph Subgraphs + Command Handoffs** | Single Giant Graph, Hierarchical Agents (Old) | **模块化**。每个 Agent 独立编译为 Subgraph，通过 `Command(goto=...)` 实现控制流跳转，支持复杂的嵌套与人工介入。 |
| **LLM 框架** | **LangChain + DeepAgents** | Raw OpenAI API | **生态复用**。DeepAgents 提供了经过验证的 Research 模板，LangChain 提供了统一的 Tool/Model 接口。 |

---

## 2. 详细技术方案

### 2.1 混合检索 (Hybrid Search) 实现
基于 PostgreSQL 实现 "Vector + Keyword" 的 Reciprocal Rank Fusion (RRF)。

**Schema 设计**:
```sql
CREATE TABLE paper_chunks (
    id UUID PRIMARY KEY,
    paper_id UUID REFERENCES papers(id),
    content TEXT,
    embedding vector(1536),  -- 适配 OpenAI/SiliconFlow 维度
    metadata JSONB           -- 存页码、章节等
);

-- 索引
CREATE INDEX ON paper_chunks USING GIN (to_tsvector('english', content)); -- 关键词
CREATE INDEX ON paper_chunks USING hnsw (embedding vector_cosine_ops);    -- 语义
```

**检索逻辑 (Python)**:
```python
def hybrid_search(query: str, k=60):
    sql = """
    WITH semantic AS (
        SELECT id, RANK() OVER (ORDER BY embedding <=> %(emb)s) as rank
        FROM paper_chunks ...
    ),
    keyword AS (
        SELECT id, RANK() OVER (ORDER BY ts_rank_cd(to_tsvector('english', content), query) DESC) as rank
        FROM paper_chunks, plainto_tsquery('english', %(query)s) query ...
    )
    SELECT id, 
           COALESCE(1.0/(%(k)s + semantic.rank), 0) + COALESCE(1.0/(%(k)s + keyword.rank), 0) as score
    FROM semantic FULL JOIN keyword ON semantic.id = keyword.id
    ORDER BY score DESC
    """
    # 执行查询...
```

### 2.2 PDF 解析与上下文工程
**流程**:
1.  **Upload**: 用户上传 PDF。
2.  **Conversion (Marker)**: 
    ```python
    from marker.converters.pdf import PdfConverter
    converter = PdfConverter(artifact_dict=create_model_dict())
    rendered = converter("paper.pdf")
    markdown_text = rendered.markdown
    ```
3.  **Cleaning**: 移除 Markdown 中的冗余 Meta 信息，提取 References。
4.  **Chunking**: 按章节 (Header) 或固定 Token 窗口切分。
5.  **Ingestion**: 存入 PG `paper_chunks` 表。

### 2.3 LangGraph 编排模式
采用 **Supervisor-Worker** 模式，但通过 `Command` 对象实现更灵活的跳转。

**主图 (Main Graph)**:
*   Nodes: `supervisor`, `research_agent` (Subgraph), `summarize_agent` (Subgraph).
*   Edges: `supervisor` 根据用户意图路由到对应 Subgraph。

**子图交互 (Subgraph Handoff)**:
```python
# 在 Subgraph 内部返回 Command 跳转回父图或其他节点
def some_node(state):
    return Command(
        goto="supervisor", 
        update={"messages": [ToolMessage(...)]},
        graph=Command.PARENT # 关键：跨图跳转
    )
```

**人工介入 (Human-in-the-loop)**:
*   使用 `interrupt_before=["human_review_node"]`。
*   用户在前端确认后，后端调用 `graph.invoke(Command(resume="approved"))` 继续执行。

---

## 3. 风险与对策
1.  **Marker 性能**: Marker 转换速度较慢 (尤其是开 OCR 时)。
    *   *对策*: 异步后台任务处理解析，前端显示进度条；提供 "纯文本模式" (PyMuPDF) 作为快速降级方案。
2.  **PGVector 维度**: 需确认生产环境 PG 版本是否支持 `vector` 扩展。
    *   *对策*: 部署脚本需包含 PGVector 编译安装步骤 (Docker 镜像)。
3.  **Token 消耗**: 论文全文 Context 极大。
    *   *对策*: 严格的 Chunking 策略；RAG 检索 Top-K；长文总结采用 Map-Reduce 模式 (LangGraph 易于实现)。

## 4. 结论
技术路径已清晰。
- **立即执行**: T-011 (详细设计)，基于上述选型定义具体的 State Schema 和 API 接口。
- **资源需求**: 需确认服务器 GPU 资源以运行 Marker (或使用 CPU 慢速模式)，或者直接调用 SiliconFlow 的 OCR API (如果成本允许)。鉴于本地部署要求，优先本地 CPU/GPU Marker。

