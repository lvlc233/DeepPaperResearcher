# BackendAgent 记忆文档

## 项目核心概念理解

### 项目整体目标
- DeepResearcher：基于 LangGraph 的 AI 辅助论文研究与管理平台
- 采用"3+1"层后端架构（Controller + Service + Infrastructure + Data）
- 通过严格的工作流（AGENT开发 → SUBMISSION提交 → 主项目合并）进行迭代

### BackendAgent 职责
- 负责后端业务逻辑的实现
- 专注于 Controller、Service、Infrastructure、Data 层的开发
- 严格遵守资源约束（仅在 AGENT/BackendAgent/ 目录下操作）
- 所有代码需经管理员审核后方可合并至主项目

## 当前任务理解

### 任务 v0.2 - 核心服务与数据库构建 (T-016, T-017)
**目标**：构建后端核心数据底座与文件处理服务

**技术范围**：
- **Data**: SQLModel + PGVector 实现用户、论文、向量切片模型
- **Service**: 论文上传、状态管理、PDF解析、向量化
- **Worker**: Arq 异步任务队列处理耗时操作
- **Infrastructure**: PDF解析器 (Marker/PyMuPDF), Embedding服务 (OpenAI/Ollama)

**关键约束**：
- **导包规范**：严禁使用 `.../` 相对导入，必须使用绝对导入（如 `from base.arxiv.parser import ...`）
- **目录规范**：
    - ORM 实体必须在 `src/base/pg/entity.py`
    - Service 必须在 `src/service/papers/`
- **时间戳**：使用中国上海时区

## 技术栈认知

### 后端核心依赖
- **Web框架**: FastAPI
- **数据库**: PostgreSQL (数据) + pgvector (向量)
- **ORM**: SQLModel
- **异步队列**: Arq + Redis
- **依赖管理**: uv
- **PDF解析**: marker-pdf / PyMuPDF
- **Embedding**: OpenAI / Ollama

## 开发模式记忆

### 分层架构规则 (严格执行)
- **Controller**: `src/controller/` - 路由、参数校验、鉴权
- **Service**: `src/service/` - 业务逻辑编排
- **Infrastructure**: `src/base/` - 基础组件 (DB, Redis, PDF Parser, Arxiv Client)
- **Data**: `src/base/pg/entity.py` (ORM), `src/business_model/` (Pydantic schemas)

### 导包规范 (2026-01-08 新增)
- ❌ 错误：`from ...base.arxiv.parser import ArxivXmlParser`
- ✅ 正确：`from base.arxiv.parser import ArxivXmlParser` (假设在src目录下)
- 这里的根目录通常指 `src` 目录被添加到 python path 中，或者使用完整的包路径。

## 项目演进历史

### 阶段一：基础功能 v0.1 (2026-01-02)
- 完成基础 Arxiv 论文获取接口
- 确立 Controller-Service-Infra 分层架构
- 修复安全漏洞与依赖注入问题

### 阶段二：系统设计 (2026-01-07)
- **需求分析**: 确定 User, Paper, Chat 核心实体与交互流程
- **技术选型**: 确认使用 Arq 处理异步任务，PGVector 存向量
- **接口设计**: 定义 `/auth`, `/papers`, `/chat` 路由规范

### 阶段三：核心实现 (2026-01-08)
- **数据库模型**: 实现 `User`, `Paper`, `PaperChunk`, `ChatSession` (位于 `base/pg/entity.py`)
- **PaperService**: 实现文件上传与状态流转 (位于 `service/papers/paper_service.py`)
- **Worker**: 集成 Arq 实现 PDF 异步解析与向量化 (`worker/tasks.py`)
- **Infrastructure**:
    - `base/pdf_parser`: 封装 Marker/PyMuPDF
    - `base/embedding`: 封装 OpenAI/Ollama

### 阶段四：用户与认证模块 (2026-01-12)
- **Auth Module**: 完成登录、注册、JWT认证 (Controller, Service, Infra)
- **测试覆盖**: 完成 Auth 模块集成测试 (Mock Service)

### 阶段五：搜索与收藏模块 (2026-01-14)
- **Search Module**: 实现论文上传、PDF解析 (PyMuPDF)、TOC提取、异步向量化 (Arq)。
- **Collection Module**: 实现收藏夹 CRUD 及论文关联功能。
- **Reading Module**: 实现目录 (TOC) 加载与文件流服务。

## 关键经验与教训 (最新)

### 架构与路径修正 (2026-01-08)
1. **ORM位置**: 之前错误放在 `business_model`，现已强制统一到 `src/base/pg/entity.py`。
2. **Service位置**: 之前错误放在 `base/service`，现已强制统一到 `src/service/papers/`。
3. **导入路径**: 相对导入（`...`）会导致模块解析错误，必须使用绝对路径或基于根模块的导入。

### 异步任务处理
- 耗时操作（PDF解析、Embedding）必须通过 Arq 异步化，避免阻塞 Web 线程。
- 任务状态需要持久化到数据库，以便前端轮询或 SSE 推送。
- **PDF处理流**: Upload -> Temp Storage -> Async Parse (Marker/PyMuPDF) -> Persistent Storage (MinIO/Local) -> Vector DB.

### 统一响应规范 (2026-01-12)
- Controller 层统一使用 `Response.success(data=...)` 返回数据，而非直接返回字典。
- 异常处理统一通过 `Response.fail` 或抛出业务异常。

### 依赖注入 (2026-01-12)
- FastAPI Dependency (`Depends`) 函数应返回具体的业务对象（如 `User` 实体），而非封装好的 `Response` 对象。
- `Response` 封装应仅在最终的 Endpoint Handler 中进行，避免在中间层导致类型校验失败。
- **Service依赖标准化**: 所有 Service 应该提供 `get_service` 工厂函数和 `ServiceDep` 类型别名 (使用 `Annotated`)。
  - 示例: `PaperServiceDep = Annotated[PaperService, Depends(get_paper_service)]`
  - 目的: 统一管理 Session 生命周期，避免 Controller 层重复编写 `Depends(get_service)`。

### 操作日志规范 (2026-01-14 强调)
- **严禁覆盖**: `OPERATION_LOG.md` 必须使用追加模式更新。
- **历史保留**: 所有的操作记录都是项目演进的重要依据，不得删除。
- **日志恢复**: 若发生覆盖，需立即根据 Git 记录或上下文恢复。

### 任务状态管理 (2026-01-14)
- **Review First**: 完成开发后，任务状态应先标记为 `🔵` (Review)，待 User 确认或自动化测试通过后再转为 `🟢` (Completed)。
- **Status Correction**: 若未经过审核直接标记为 Completed，需回退状态至 Review。

### 数据库会话管理 (2026-01-12 新增)
- **分离依赖与上下文管理器**: 
    - `get_session_dependency`: 仅作为 Generator 用于 FastAPI `Depends`，由框架管理生命周期。
    - `get_db_session`: 被 `@asynccontextmanager` 装饰，用于 Service 层 `async with`。
- **显式资源释放**: 在 Generator 中使用 `try...except...finally` 结构，确保 `session.close()` 即使在异常时也能执行，防止 `ConnectionDoesNotExistError`。
- **避免混合使用**: 不要在 Generator 内部再使用 `async with session_factory()`，而是显式创建和关闭，避免双重 Context Manager 导致的逻辑混乱。

### PDF解析与搜索配置 (2026-01-15)
- **Marker库适配**: 新版 `marker-pdf` 废弃了 `load_all_models`，需使用 `PdfConverter` + `create_model_dict` 初始化。
- **解析器架构**: CPU密集型解析任务（如Marker渲染）必须封装在 `asyncio` executor 中运行，避免阻塞主线程。
- **搜索配置管理**: 搜索相关参数（深度推理、自动摘要等）已纳入用户设置体系 (`UserSettings`)，通过 `/api/v1/search/config` 统一管理。

### 架构决策与技术债务 (2026-01-16)
- **共享模型模式 (Shared Schema Pattern)**:
  - **现状**: Reader 模块 (`src/service/reader/schema.py`) 采用了共享模型模式，Service 层定义的 Schema 同时被用作 Controller 层的 Request/Response 模型。
  - **原因**: 为了快速迭代，减少 CRUD 类业务的重复样板代码。
  - **规范偏差**: 这不符合严格的分层架构规范（Controller 应定义 Request/Response，Service 应定义 DTO）。
  - **未来规划**: 这是一个已知的技术债务，后续需要重构为 Mapper 模式 (Request -> DTO -> Response)。目前通过 TODO 注释标记。

### 配置服务重构 (2026-01-16)
- **异步升级**: `ConfigService` 已完全重构为异步模式，支持 `AsyncSession`，消除了同步 DB 操作带来的性能隐患。
- **依赖注入**: 修复了 `SettingsRouter` 中的依赖注入错误，统一使用 `SessionDep`。
- **用户配置双轨制 (现状)**:
  - `User.settings` (JSON列): 存储简单的、非结构化的用户偏好 (Legacy)。
  - `UserConfigValue` (Table): 存储复杂的、系统定义的配置项 (推荐)。
  - **TODO**: 未来需要合并这两套配置系统。

### 类型检查 (2026-01-20)
应该使用mypy进行类型检查，以确保代码的类型安全。
### 数据库架构重构 (2026-01-20)
- **AgentSession 确立**: 废弃并移除了 `ChatSession` 实体。
- **单一会话实体**: `AgentSession` 成为管理所有对话和 Agent 运行上下文的唯一实体。
- **关联关系**: `AgentSession` 直接通过 `paper_id` 关联 `Paper`，通过 `user_id` 关联 `User`。
- **修正**: 修复了 SQLAlchemy Mapper 错误，确保 `User` 和 `Paper` 的反向关系 (`back_populates`) 正确指向 `AgentSession`。

---
**最后更新**: 2026年01月20日 11:30
**记忆版本**: v1.11
