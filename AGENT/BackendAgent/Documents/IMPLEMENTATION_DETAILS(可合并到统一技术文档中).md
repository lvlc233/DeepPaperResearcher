# 后端实现细节文档 (Database & Interface)

**文档信息**
- **负责人**: BackendAgent
- **日期**: 2026-01-07
- **关联任务**: T-014
- **版本**: v1.0

---

## 1. 数据库设计 (Database Design)

基于 `SQLModel` 和 `PostgreSQL` (pgvector)，采用 Code-First 模式。

### 1.1 基础模型与配置
所有模型继承自 `SQLModel`。

### 1.2 用户模块 (User Module)

```python
# src/data/models/user.py
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from typing import Optional

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 1.3 论文模块 (Paper Module)

核心业务数据，包含论文元数据和向量切片。

#### Paper (元数据)
```python
# src/data/models/paper.py
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship

class PaperStatus(str, Enum):
    PENDING = "pending"       # 等待处理
    PROCESSING = "processing" # 处理中 (下载/解析/向量化)
    COMPLETED = "completed"   # 处理完成
    FAILED = "failed"         # 处理失败

class Paper(SQLModel, table=True):
    __tablename__ = "papers"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    title: str = Field(index=True)
    authors: Optional[str] = None # JSON string or comma separated
    abstract: Optional[str] = None
    
    file_key: str  # MinIO Object Key
    file_url: Optional[str] = None # Presigned URL (temporary) or Public URL
    
    status: PaperStatus = Field(default=PaperStatus.PENDING)
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    chunks: List["PaperChunk"] = Relationship(back_populates="paper")
```

#### PaperChunk (向量切片)
使用 `pgvector` 存储 Embedding。

```python
# src/data/models/paper.py (continued)
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column

class PaperChunk(SQLModel, table=True):
    __tablename__ = "paper_chunks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    paper_id: UUID = Field(foreign_key="papers.id", index=True)
    
    content: str # 切片文本内容
    page_number: Optional[int] = None
    chunk_index: int # 在原文中的顺序
    
    # Vector Field (OpenAI text-embedding-3-small: 1536 dim)
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))
    
    paper: Paper = Relationship(back_populates="chunks")
```

### 1.4 对话模块 (Chat Module)

用于存储 Agent 对话历史。

```python
# src/data/models/chat.py
from typing import List, Optional, Any
from pydantic import SerializeAsAny

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    messages: List["ChatMessage"] = Relationship(back_populates="session")

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_sessions.id", index=True)
    
    role: str # "user", "assistant", "system"
    content: str
    
    # 引用来源 (存储 JSON 结构: [{"paper_id": "...", "chunk_id": "...", "score": 0.9}])
    sources: Optional[str] = None 
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    session: ChatSession = Relationship(back_populates="messages")
```

### 1.5 收藏夹模块 (Collection Module)

用于管理用户的论文收藏夹。

```python
# src/base/pg/entity.py

class Collection(SQLModel, table=True):
    __tablename__ = "collections"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="collections")
    # papers: Link through CollectionPaper

class CollectionPaper(SQLModel, table=True):
    __tablename__ = "collection_papers"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    collection_id: UUID = Field(foreign_key="collections.id")
    paper_id: UUID = Field(foreign_key="papers.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 2. 接口设计 (API Interface Design)

遵循 RESTful 规范，URL 前缀 `/api/v1`。

### 2.1 认证 (Auth) - Tags: `Auth`

| Method | Path | Summary | Request | Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/auth/login` | 用户登录 (OAuth2 Password) | `OAuth2PasswordRequestForm` | `Token` (access_token, token_type) |
| POST | `/auth/refresh` | 刷新 Token | - | `Token` |
| POST | `/auth/register`| 用户注册 | `UserCreate` | `UserRead` |

### 2.2 用户 (Users) - Tags: `Users`

| Method | Path | Summary | Request | Response |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/users/me` | 获取当前用户信息 | - | `UserRead` |
| PUT | `/users/me` | 更新当前用户信息 | `UserUpdate` | `UserRead` |

### 2.3 论文管理 (Papers) - Tags: `Papers`

| Method | Path | Summary | Request | Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/papers/upload` | 上传并解析论文 | `UploadFile` | `PaperRead` (Status: Pending) |
| GET | `/papers/` | 获取论文列表 (分页) | `Query(page, size, keyword)` | `Paginated[PaperRead]` |
| GET | `/papers/{id}` | 获取论文详情 | - | `PaperReadWithChunks` (含 TOC, FileURL) |
| POST | `/papers/{id}/reprocess` | 重试解析/向量化 | - | `Message` |
| DELETE | `/papers/{id}` | 删除论文 | - | `Message` |
| GET | `/papers/{id}/file` | 获取论文PDF文件流 | - | `FileResponse` |

### 2.4 收藏夹 (Collections) - Tags: `Collections`

| Method | Path | Summary | Request | Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/collections` | 创建收藏夹 | `CollectionCreate` | `CollectionResponse` |
| GET | `/collections` | 获取收藏夹列表 | `Query(limit, offset)` | `List[CollectionResponse]` |
| GET | `/collections/{id}` | 获取收藏夹详情 | - | `CollectionDetailResponse` |
| PUT | `/collections/{id}` | 更新收藏夹 | `CollectionUpdate` | `CollectionResponse` |
| DELETE | `/collections/{id}` | 删除收藏夹 | - | `204 No Content` |
| POST | `/collections/{id}/papers` | 添加论文到收藏夹 | `AddPaperRequest` | `Message` |
| DELETE | `/collections/{id}/papers/{paper_id}` | 从收藏夹移除论文 | - | `204 No Content` |

### 2.5 对话 (Chat) - Tags: `Chat`

| Method | Path | Summary | Request | Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/chat/sessions` | 创建新会话 | `SessionCreate` | `SessionRead` |
| GET | `/chat/sessions` | 获取会话列表 | - | `List[SessionRead]` |
| GET | `/chat/sessions/{id}/history` | 获取会话历史 | - | `List[MessageRead]` |
| POST | `/chat/sessions/{id}/message` | 发送消息 (Stream) | `ChatRequest` (content, mode) | `EventSourceResponse` (SSE) |

> **Chat SSE Event Format**:
> - `event: token` -> `data: "Hello"` (Token stream)
> - `event: thought` -> `data: "Thinking..."` (Agent internal thought)
> - `event: source` -> `data: JSON({...})` (Citation info)
> - `event: error` -> `data: "Error msg"`

### 2.6 搜索 (Search) - Tags: `Search`

| Method | Path | Summary | Request | Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/search` | 搜索论文 (综合) | `SearchRequest` | `SearchResponse` |
| GET | `/search/history` | 获取搜索历史 | `Query(limit)` | `List[SearchHistoryResponse]` |
| DELETE | `/search/history` | 清空搜索历史 | - | `204 No Content` |
| GET | `/search/config` | 获取搜索配置 | - | `SearchSettingsResponse` |
| PUT | `/search/config` | 更新搜索配置 | `SearchSettingsUpdate` | `SearchSettingsResponse` |

---

## 3. 异步任务设计 (Async Tasks)

基于 `Arq` 实现。

### 3.1 任务定义

1.  **`task_process_paper_upload(ctx, paper_id: UUID, file_path: str)`**
    *   **步骤**:
        1.  更新 Paper Status -> `PROCESSING`
        2.  调用 Marker 解析 PDF -> Markdown
        3.  Text Splitter 切分文本
        4.  调用 LLM Embedding API 获取向量
        5.  批量写入 `PaperChunk` 表
        6.  更新 Paper Status -> `COMPLETED`
    *   **异常处理**: 捕获异常，更新 Status -> `FAILED`，记录 `error_message`。

2.  **`task_cleanup_failed_uploads(ctx)`** (Cron)
    *   定期清理上传了但未在数据库记录的文件，或长期处于 `PROCESSING` 的僵尸任务。

---

## 4. 安全设计 (Security)

1.  **Password**: 使用 `bcrypt` (Passlib) 哈希存储。
2.  **Token**: 使用 `JWT` (HS256)，包含 `sub` (user_id) 和 `exp`。
3.  **CORS**: 允许前端域名跨域。
4.  **Input Validation**: 严格依赖 Pydantic Models。
