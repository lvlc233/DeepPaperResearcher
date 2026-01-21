# 后端技术选型与架构设计文档

**文档信息**
- **负责人**: BackendAgent
- **日期**: 2026-01-07
- **关联任务**: T-013
- **版本**: v1.0

---

## 1. 核心技术栈决策

基于 Context7 的深度调研与项目“轻量级 + 高性能”的需求，做出以下技术决策：

### 1.1 Web 框架: FastAPI (Async)
*   **版本**: Latest (0.115+)
*   **理由**: 
    *   原生支持 Python `async/await`，处理高并发 I/O (数据库、网络请求) 性能优异。
    *   基于 Pydantic 的自动数据验证与 OpenAPI 文档生成。
    *   **SSE 支持**: 利用 `sse-starlette` 或原生 `StreamingResponse` 实现 Agent 流式对话。

### 1.2 异步任务队列: Arq
*   **决策**: **Arq** (vs Celery/FastStream)
*   **理由**:
    *   **极度轻量**: 仅依赖 `redis` 和 `asyncio`，无复杂 Broker/Backend 配置。
    *   **原生异步**: 设计之初即为 Async IO，完美契合 FastAPI。
    *   **功能够用**: 支持延时任务、定时任务、重试机制，足以应对 "PDF 解析" 和 "长 Agent 任务"。
    *   *调研数据*: Benchmark Score 70.2 (High Reputation), 代码片段丰富。

### 1.3 数据库与 ORM: SQLModel + PGVector
*   **数据库**: PostgreSQL 15+ (开启 `vector` 扩展)
*   **ORM**: **SQLModel** (Pydantic + SQLAlchemy)
*   **理由**:
    *   **统一模型**: SQLModel 允许使用同一个 Class 既作为 Pydantic 模型 (API 交互) 又作为 SQLAlchemy 模型 (数据库映射)，减少代码重复。
    *   **向量支持**: `pgvector-python` 提供了 SQLAlchemy 的 `Vector` 类型，可直接集成到 SQLModel 中。
    *   **混合检索**: 通过原生 SQL (利用 `Session.exec`) 实现 Vector + Keyword (Full-Text) 的 RRF 融合排序。

### 1.4 向量检索: PGVector (Hybrid Search)
*   **架构**: 不引入额外的 Vector DB (如 Milvus/Chroma)，直接利用 PG。
*   **实现**:
    *   **语义检索**: HNSW 索引 (`vector_cosine_ops`)。
    *   **关键词检索**: GIN 索引 (`to_tsvector`)。
    *   **融合**: 使用 SQL `CTE` (Common Table Expressions) 和 `Rank` 函数实现倒数排名融合 (RRF)。

### 1.5 文件存储: MinIO (Local S3)
*   **决策**: **MinIO**
*   **理由**: 提供兼容 S3 的 API，方便未来迁移至云端，且支持预签名 URL (Presigned URL) 供前端直接下载，减轻后端流量压力。

---

## 2. 详细架构设计

### 2.1 目录结构 (Refined)
在 `SPECIFICATION.md` 基础上细化：

```text
main/backend/src/
├── app/                        # 应用入口
│   ├── main.py                 # FastAPI App 初始化
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 环境变量 (Pydantic Settings)
│   │   ├── events.py           # Startup/Shutdown 事件 (DB 连接, Arq Pool)
│   │   └── exceptions.py       # 全局异常处理
│   └── api/                    # 路由定义 (V1)
│       └── v1/
│           ├── api.py          # 路由聚合
│           └── endpoints/      # 具体业务接口
│               ├── auth.py
│               ├── papers.py
│               ├── collections.py  # 收藏夹管理
│               └── agent.py
├── service/                    # 业务逻辑层 (Service Layer)
│   ├── paper_service.py        # 论文管理 (CRUD, 调度解析)
│   ├── collection_service.py   # 收藏夹逻辑
│   ├── agent_service.py        # Agent 调用与流式处理
│   └── auth_service.py         # 用户认证
├── worker/                     # 异步任务消费者
│   ├── main.py                 # Arq Worker 入口
│   └── tasks/                  # 具体任务函数
│       ├── paper_tasks.py      # PDF 解析 (PyMuPDF), 向量化
│       └── email_tasks.py      # (可选) 邮件发送
├── data/                       # 数据访问层 (Data Layer)
│   ├── db.py                   # 数据库连接 (AsyncEngine)
│   ├── redis.py                # Redis 连接池
│   └── models/                 # SQLModel 模型
│       ├── user.py
│       ├── paper.py            # Paper, PaperChunk (含 Vector)
│       └── entity.py           # 统一实体定义 (Collection, etc.)
├── infra/                      # 基础设施/第三方客户端
│   ├── storage/                # MinIO/S3 客户端
│   ├── llm/                    # LLM Client (OpenAI/SiliconFlow)
│   └── parser/                 # PDF Parser (Marker/PyMuPDF) 封装
└── utils/                      # 通用工具
    ├── security.py             # JWT, Password Hash
    └── common.py
```

### 2.2 数据库 Schema 设计 (Concept)

#### Paper (论文元数据)
```python
class Paper(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True)
    abstract: str | None
    url: str | None
    storage_path: str           # MinIO 中的路径
    status: str                 # 'pending', 'processing', 'completed', 'failed'
    created_at: datetime
    # Relationships...
```

#### PaperChunk (向量切片)
```python
from pgvector.sqlalchemy import Vector

class PaperChunk(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    paper_id: UUID = Field(foreign_key="paper.id")
    content: str
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))  # 核心：向量列
    page_number: int
```

### 2.3 异步任务流程 (Arq)

1.  **生产者 (FastAPI Endpoint)**:
    ```python
    # POST /papers/upload
    await redis.enqueue_job('process_pdf_task', paper_id=new_paper.id)
    ```
2.  **消费者 (Arq Worker)**:
    ```python
    # worker/tasks/paper_tasks.py
    async def process_pdf_task(ctx, paper_id: UUID):
        # 1. Download PDF from MinIO
        # 2. Call Marker to parse to Markdown
        # 3. Chunk text
        # 4. Generate Embeddings (LLM API)
        # 5. Save to PG (PaperChunk)
        # 6. Update Paper status
    ```

### 2.4 Agent 流式交互 (SSE)

采用 `sse-starlette` 的 `EventSourceResponse`:

```python
# service/agent_service.py
async def chat_stream(agent_input):
    async for event in agent_graph.astream_events(agent_input, version="v1"):
        if event["event"] == "on_chat_model_stream":
            yield {"event": "token", "data": event["data"]["chunk"].content}
        # 处理 tool_start, tool_end 等事件...

# api/v1/endpoints/agent.py
@router.post("/chat")
async def chat(request: ChatRequest):
    return EventSourceResponse(chat_stream(request))
```

---

## 3. 环境与依赖版本 (Constraints)

*   `python` >= 3.12
*   `fastapi` >= 0.115.0
*   `sqlmodel` >= 0.0.16
*   `pydantic` >= 2.0
*   `arq` >= 0.26.0
*   `asyncpg` >= 0.29.0
*   `pgvector` >= 0.2.0
*   `minio` >= 7.2.0
*   `sse-starlette` >= 2.1.0

## 4. 结论

本方案采用 **FastAPI + Arq + SQLModel (PGVector)** 的黄金组合，既保证了开发效率（Python 原生异步、统一模型），又满足了高性能需求（异步任务、混合检索）。无需引入重型组件（如 Celery/RabbitMQ/Elasticsearch），完美契合“轻量级”的项目定位。

**下一步 (T-014)**: 依据此文档，正式创建数据库模型代码和 API 接口定义。
