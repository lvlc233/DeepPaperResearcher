# BackendAgent(python) 核心知识库

> 记录开发过程中的关键经验、设计原则与最佳实践。

## 1. API 设计与数据模型
### 1.1 防止数据模型穿透 (Data Model Penetration)
- **原则**: 严禁直接将数据库实体 (Entity/Model) 作为 API 响应返回给前端。
- **原因**: 数据库实体往往包含内部字段（如 `password`, `is_deleted`, `description` 等），直接暴露可能导致敏感信息泄露或传输冗余数据。
- **实践**:
    - 必须为每个 API 定义独立的 **Response DTO** (Pydantic Model)。
    - 使用 `model_validate` 或 `from_attributes=True` 将 Entity 转换为 Response DTO。
    - 显式定义 Response DTO 的字段，仅包含前端真正需要的数据。
    - **案例**: 收藏夹 `Collection` 实体包含 `description`，但 API 响应 `CollectionResponse` 移除该字段，仅保留 `id`, `name`, `total` 等。

### 1.2 资源迁移接口设计
- **场景**: 将资源 A (Paper) 从容器 B (Collection 1) 移动到容器 C (Collection 2)。
- **原则**: 优先使用 **PATCH** 方法作用于目标资源或父资源，表达“修改归属”的语义。
- **实践**:
    - **路径**: `PATCH /collections/{target_id}/papers/move/{paper_id}`
    - **语义**: “修改目标收藏夹，使其包含该论文（隐含从旧处移除）”。
    - **原子性**: 迁移操作必须是原子的（Remove from Old + Add to New），避免数据不一致。

## 2. 测试策略
### 2.1 FastAPI 路由测试
- **Mock 依赖**: 使用 `app.dependency_overrides` 替换真实的 Service 层。
- **验证逻辑**:
    - 不仅验证 HTTP Status Code (200/400)。
    - **必须验证 Service 方法调用的参数** (`mock_service.method.assert_called_with(...)`)，确保路由层正确解析并传递了参数（如 `user_id`, `paper_id`）。
    - **案例**:
      ```python
      mock_collection_service.move_paper.assert_called_once()
      args, kwargs = mock_collection_service.move_paper.call_args
      assert args[0] == paper_id
      assert args[1] == collection_id
      ```

## 3. 工程规范
- **日志**: 每次变更需在 `LOG/YYYY-MM-DD.md` 中记录时间、目标、范围与验证结果。
- **文件操作**: 优先修改现有文件，避免创建过多零散文件。
