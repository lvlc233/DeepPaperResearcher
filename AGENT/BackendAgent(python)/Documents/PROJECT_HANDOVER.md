# 项目交接备忘录 (Project Handover Note)

**日期**: 2026-01-21
**创建人**: BackendAgent(python)
**状态**: 准备切换至“阉割版本”

---

## 1. 关键技术决策 (Key Decisions)

### 1.1 搜索服务回退机制 (Search Fallback)
- **背景**: 用户在项目初期未上传本地论文时，默认搜索仅针对本地数据库，导致搜索结果为空，用户体验极差。
- **决策**: 在后端 `SearchService` 中实现了自动回退逻辑。
- **逻辑**: 
    - 优先搜索本地数据库。
    - 若本地搜索结果为 `0` 且请求未显式指定 `source='local'`，系统自动调用 `ArxivService` 进行外部搜索。
- **代码位置**: `src/service/search/search_service.py` -> `search_papers` 方法。

### 1.2 防御性编程策略 (Defensive Programming Policy)
- **决策**: **移除过度的防御性编程**，倾向于让错误尽早暴露（Fail Fast）。
- **前端调整**: 
    - 移除了 `SearchResults.tsx` 和 `paper.service.ts` 中对 API 返回数据的 `Array.isArray` 校验。
    - 假设后端契约始终可靠，若后端返回错误格式，前端应直接报错而非静默处理。
- **后端调整**:
    - 移除了 `SearchService` 中对 `session_name` 为空时的默认值生成逻辑。
    - 依赖数据库的 `NOT NULL` 约束来保证数据质量，遇到非法数据直接抛出 `IntegrityError`。

### 1.3 架构规范 (Architecture Standards)
- **三层架构**: Controller (Router) -> Service -> Repository (Infrastructure)。
- **模型分层**:
    - **Controller 层**: 仅定义 `Request` / `Response` 模型 (Pydantic)。
    - **Service 层**: 定义业务实体 `DTO`，负责业务逻辑和数据组装。
    - **Infrastructure 层**: 定义数据库实体 `SQLModel` / `SQLAlchemy`。
    - **禁止越级**: Service 层不应直接依赖 Controller 层的 Request/Response 模型；Controller 层也不应直接操作数据库实体。

---

## 2. 待办事项与已知问题 (Todos & Known Issues)

### 2.1 待迁移/阉割功能
- 切换到“阉割版本”时，需确认是否保留 `ArxivService` 的完整功能，还是仅保留基础存根。
- 确认是否需要精简数据库表结构（如移除复杂的 `Job` 或 `View` 相关表）。

### 2.2 潜在风险
- 移除防御性编程后，若后端 API 契约发生变更（如返回格式改变），前端页面可能会直接崩溃（白屏）。建议在“阉割版本”中保持前后端版本的高度一致性。

---

## 3. 环境与依赖
- **Python**: 3.12+
- **Database**: PostgreSQL (with pgvector)
- **Backend Framework**: FastAPI
- **ORM**: SQLModel / SQLAlchemy (Async)

---
*此文档用于辅助项目版本切换，请接手人员仔细阅读。*
