# 后端组件文档 (Backend Component Documentation)

**负责人**: BackendAgent  
**最后更新**: 2026-01-12  
**描述**: 本文档将后端的各层级（Controller, Service, Repository, Entity）视为可复用的组件，详细记录其接口定义、职责范围及使用方法。

---

## 1. 核心架构设计 (Core Architecture)

本项目采用经典的分层架构 (Layered Architecture)，确保关注点分离：

*   **Controller Layer (API组件)**: 
    *   **职责**: 处理 HTTP 请求/响应，参数校验 (Pydantic)，权限控制 (Depends)。
    *   **原则**: 不包含复杂业务逻辑，仅进行数据适配和 Service 调用。
*   **Service Layer (业务组件)**: 
    *   **职责**: 核心业务逻辑封装，事务管理，编排 Repository 和外部服务 (PDF Parser, Embedding)。
    *   **原则**: 返回 DTO (Data Transfer Object) 而非 Entity，屏蔽底层数据结构。
*   **Repository Layer (数据组件)**: 
    *   **职责**: 数据库 CRUD 操作封装，执行 SQL 语句。
    *   **原则**: 仅处理 Entity 对象，不包含业务逻辑。
*   **Entity Layer (模型组件)**: 
    *   **职责**: 数据库表结构映射 (SQLModel)。

---

## 2. 基础设施组件 (Infrastructure Components)

### 2.1 Database (PostgreSQL + pgvector)
**路径**: `src/base/pg/`

*   **Connection**: `src/base/pg/service.py`
    *   **Function**: `get_db_session()`
    *   **Usage**: FastAPI Dependency Injection
    ```python
    @router.get("/")
    async def endpoint(session: AsyncSession = Depends(get_db_session)):
        ...
    ```

### 2.2 PDF Parser
**路径**: `src/base/pdf_parser/parser.py`

**描述**: 
提供统一的 PDF 解析接口，支持多种解析引擎 (PyMuPDF, Marker)。

**API**:
*   `extract_pdf_text(file_path: Path, parser_type: str = "auto") -> str`
    *   **输入**: PDF 文件绝对路径。
    *   **输出**: 提取的纯文本内容。
*   `parse_pdf(file_path: Path, parser_type: str = "auto") -> PDFParseResult`
    *   **输出**: 结构化解析结果 (文本, 元数据, 章节结构)。

**依赖**: `pymupdf` (fitz) 或 `marker-pdf`。

### 2.3 Embedding Service
**路径**: `src/base/embedding/embedding_service.py`

**描述**: 
提供文本向量化服务，支持 OpenAI 接口及本地 ONNX 模型 (BGE-M3)。

**API**:
*   `embed_batch(texts: List[str], model_type: str = "openai") -> List[List[float]]`
    *   **输入**: 文本片段列表。
    *   **输出**: 向量列表 (Dimension: 1536 for OpenAI, 1024 for BGE-M3)。

---

## 3. 业务模块组件 (Business Modules)

### 3.1 认证模块 (Auth Module)
**职责**: 处理用户注册、登录、身份校验及 Token 管理。

#### [Controller] AuthRouter
**路径**: `src/controller/api/auth/router.py`
**接口前缀**: `/api/v1/auth`

**Endpoints**:
*   `POST /login`
    *   **Request**: `UserLogin` (email, password)
    *   **Response**: `Token` (access_token, token_type, user)
*   `POST /register`
    *   **Request**: `UserCreate` (email, password, full_name)
    *   **Response**: `UserResponse`
*   `GET /users/me`
    *   **Response**: `UserResponse`

#### [Service] AuthService
**路径**: `src/service/auth/auth_service.py`

**依赖注入**:
```python
async def get_auth_service(session: SessionDep) -> AuthService: ...
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
```

**Core Methods**:
*   `authenticate_user(email, password) -> User`: 验证凭据，成功返回 User。
*   `create_user(email, password, ...) -> User`: 注册新用户，包含密码哈希。
*   `get_user_by_token(token) -> User`: JWT 解码并获取当前用户 (用于 `get_current_user` 依赖)。

#### [Infrastructure] Security
**路径**: `src/common/security.py`
*   `verify_password(plain, hashed) -> bool`: 密码校验 (bcrypt)。
*   `create_access_token(subject) -> str`: 生成 JWT Token。

#### [Schema] Auth Models
**路径**: `src/controller/api/auth/schema.py`

```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
```

---

### 3.2 论文模块 (Papers Module)
**职责**: 论文的上传、解析、检索、管理及状态追踪。

#### [Controller] PapersRouter
**路径**: `src/controller/api/papers/router.py`
**接口前缀**: `/api/v1/papers`

**Endpoints**:
*   `GET /`
    *   **Query**: `limit=10`, `offset=0`
    *   **Response**: `List[PaperStatusResponse]`
*   `POST /upload`
    *   **Form**: `file` (UploadFile), `title` (Optional), `authors` (Optional)
    *   **Response**: `PaperUploadResponse`
*   `GET /{id}`
    *   **Response**: `PaperDTO`
*   `GET /search/{query}`
    *   **Response**: `SearchResponse`

#### [Service] PaperService
**路径**: `src/service/papers/paper_service.py`

**Core Methods**:
*   `upload_paper(...)`
    *   **Logic**: 验证文件 -> 保存到 MinIO/Local -> 创建 DB 记录 -> 触发 `process_pdf` 异步任务。
*   `get_user_papers(...)`
    *   **Logic**: 查询 DB -> 转换为 DTO -> 返回列表。
*   `process_pdf(paper_id: UUID) -> bool` (in `PaperProcessingService`)
    *   **Logic**: PDF Parse -> Split Text -> Embedding -> Save Chunks -> Update Status.

#### [Schema] Paper Models
**路径**: `src/service/papers/schema.py`

```python
class PaperDTO(BaseModel):
    id: UUID
    title: str
    status: PaperStatus # PENDING, PROCESSING, COMPLETED, FAILED
    file_key: str
    ...
```

---

### 3.3 阅读器模块 (Reader Module)
**职责**: 管理阅读器状态，包括图层 (Layers) 和 标注 (Annotations)。

#### [Controller] ReaderRouter
**路径**: `src/controller/api/reader/router.py`
**接口前缀**: `/api/v1/reader`

**Endpoints**:
*   `GET /{paper_id}/layers`
    *   **Response**: `LayerListResponse`
*   `POST /layers`
    *   **Request**: `LayerCreate` (name, type, visible)
    *   **Response**: `LayerResponse`
*   `POST /annotations`
    *   **Request**: `AnnotationCreate` (layer_id, type, rects, content, color)
    *   **Response**: `AnnotationResponse`
*   `PUT /annotations/{id}`
    *   **Request**: `AnnotationUpdate`
*   `DELETE /annotations/{id}`

#### [Schema] Reader Models
**路径**: `src/controller/api/reader/schema.py`

```python
class AnnotationCreate(BaseModel):
    type: str # 'highlight' | 'note' | 'translate'
    rects: List[Dict[str, Any]] # 坐标列表
    content: Optional[str]
    color: Optional[str]
```

---

### 3.4 对话模块 (Chat Module)
**职责**: 提供统一的对话服务，支持多 Agent (Chat/Search) 路由及 SSE 流式响应。

#### [Controller] ChatRouter
**路径**: `src/controller/api/chat/router.py`
**接口前缀**: `/api/v1/chat`

**Endpoints**:
*   `POST /sessions`
    *   **Request**: `ChatSessionCreate` (agent_type, context)
    *   **Response**: `ChatSessionResponse`
*   `POST /sessions/{id}/message`
    *   **Request**: `ChatMessageRequest` (content, files)
    *   **Response**: `text/event-stream` (SSE)

**SSE Protocol**:
*   Event: `metadata` -> Data: JSON `{ run_id, session_id }`
*   Event: `token` -> Data: String (Token content)
*   Event: `finish` -> Data: JSON `{ reason: "stop" }`

#### [Schema] Chat Models
**路径**: `src/controller/api/chat/schema.py`

```python
class ChatMessageRequest(BaseModel):
    content: str
    files: Optional[List[str]]
```

---

### 3.5 报告模块 (Reports Module)
**职责**: 深度研究报告的生成、存储与展示。

#### [Controller] ReportsRouter
**路径**: `src/controller/api/reports/router.py`
**接口前缀**: `/api/v1/reports`

**Endpoints**:
*   `POST /generate`
    *   **Request**: `ReportCreate` (type: 'deep_research' | 'related_work')
    *   **Response**: `ReportResponse` (Initial status: 'generating')
*   `GET /{id}`
    *   **Response**: `ReportResponse` (Contains markdown content)

---

### 3.6 收藏夹模块 (Collection Module)
**职责**: 管理用户的论文收藏夹，支持创建、查询、更新、删除及论文的添加/移除。

#### [Controller] CollectionRouter
**路径**: `src/controller/api/collections/router.py`
**接口前缀**: `/api/v1/collections`

**Endpoints**:
*   `POST /`
    *   **Request**: `CollectionCreate` (name, description)
    *   **Response**: `CollectionResponse`
*   `GET /`
    *   **Query**: limit, offset
    *   **Response**: `List[CollectionResponse]`
*   `GET /{collection_id}`
    *   **Response**: `CollectionDetailResponse` (包含 papers 列表)
*   `PUT /{collection_id}`
    *   **Request**: `CollectionUpdate`
    *   **Response**: `CollectionResponse`
*   `DELETE /{collection_id}`
    *   **Response**: 204 No Content
*   `POST /{collection_id}/papers`
    *   **Request**: `AddPaperRequest` (paper_id)
    *   **Response**: Success Message

#### [Service] CollectionService
**路径**: `src/service/collections/collection_service.py`

**Core Methods**:
*   `create_collection(user_id, data) -> Collection`
*   `get_user_collections(user_id, limit, offset) -> List[Collection]`
*   `get_collection_detail(collection_id, user_id) -> CollectionDetailResponse`: 聚合查询收藏夹及其包含的论文信息。
*   `add_paper_to_collection(collection_id, paper_id, user_id) -> bool`

---

## 4. 开发规范 (Development Standards)

### 4.1 接口交互规范
*   **统一前缀**: 所有 API 均挂载于 `/api/v1`。
*   **依赖注入**: 必须使用 `Annotated` + `Depends` 定义 Service 依赖。
    ```python
    # Define in service.py
    AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

    # Use in router.py
    @router.post("/login")
    async def login(
        form_data: UserLogin, 
        service: AuthServiceDep # Standardized
    ): ...
    ```

### 4.2 异常处理
*   使用 `HTTPException` 抛出错误，并在 Service 层捕获业务异常转化为 HTTP 异常或自定义 Error Code。

### 4.3 异步编程
*   所有 I/O 操作 (DB, Network, File) 必须使用 `await`。
*   CPU 密集型任务 (Parsing, Embedding) 应 offload 到 ThreadPool 或独立 Worker (Arq)。
