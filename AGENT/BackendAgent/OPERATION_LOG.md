
---

## 2026-01-16 14:00:00
**操作内容**: 修复 transformers 库的缓存路径弃用警告
**操作目标**: 将 TRANSFORMERS_CACHE 迁移至 HF_HOME，消除 FutureWarning
**操作结果**: 成功
**验证方式**: 编写测试脚本 test_config_fix.py 模拟环境并验证导入 transformers 时无警告
**备注**:
- 修改 `src/base/config.py`:
  - 在导入 transformers 之前检查并设置 HF_HOME 环境变量
  - 如果检测到 TRANSFORMERS_CACHE 且未设置 HF_HOME，则将 HF_HOME 设置为 TRANSFORMERS_CACHE 的值并移除 TRANSFORMERS_CACHE
- 验证脚本确认警告已消除且环境变量正确传递

---

## 2026-01-17 11:14
**操作内容**: 修复登录失败时的 CORS 响应头缺失
**操作目标**: 让 401/422/500 等错误响应也携带 Access-Control-Allow-Origin
**操作结果**: 成功
**验证方式**:
- 使用 TestClient 构造 Origin 请求头，验证 /api/v1/auth/login 失败时仍返回 CORS 头
- 运行 `pytest test/src/test_auth_router.py -q`（6 passed）
**变更范围**:
- `main/backend/src/controller/response.py`
- `main/backend/test/src/test_auth_router.py`
**备注**:
- 根因: 全局异常处理器返回的 JSONResponse 在某些失败路径下未带上 CORS 头，浏览器将其表现为“跨域错误”。
- 方案: 在全局异常处理器中按允许列表回显 Origin，并补齐 Allow-Credentials/Vary。

---

## 2026-01-17 12:28
**操作内容**: 补充默认收藏夹相关测试并修复 pytest 收集范围
**操作目标**: 覆盖默认收藏夹核心行为，保证全量测试可稳定通过
**操作结果**: 成功
**验证方式**:
- 运行 `python -m pytest -q`（全量通过）
- 运行 `python -m compileall -q src test`
**变更范围**:
- `main/backend/test/src/test_collection_router.py`
- `main/backend/pyproject.toml`
**备注**:
- 新增默认收藏夹服务层的补充测试用例（并发插入触发 IntegrityError 的兜底路径、offset=0 才触发 ensure_default_collection、默认收藏夹允许更新 description）。
- 将 pytest 收集范围限制在 `test/`，避免把 `src/` 下的内部调试文件误当作测试导致收集失败。

---

## 2026-01-17 12:49
**操作内容**: 移除默认用户ID的 Mock 行为并修复事务回滚错误
**操作目标**: 避免使用不存在的用户ID触发外键错误，消除 PendingRollbackError
**操作结果**: 成功
**验证方式**:
- 运行 `python -m pytest -q`（全量通过）
**变更范围**:
- `main/backend/src/base/pg/service.py`
- `main/backend/src/controller/api/collections/router.py`
- `main/backend/src/controller/api/reports/router.py`
- `main/backend/src/service/collections/collection_service.py`
- `main/backend/test/src/test_collection_router.py`
**备注**:
- 根因1: `get_current_user_id` 在缺少 Header 时返回固定 UUID，运行时会拿不存在的 user_id 写入 collections，触发外键错误。
- 根因2: `ensure_default_collection` 捕获 IntegrityError 后未 rollback，继续复用同一 Session 查询会触发 PendingRollbackError。
- 处理: 现在缺少/非法 `X-User-Id` 直接返回 401/400；默认收藏夹创建失败会先 rollback，再回查；并在服务层校验用户是否存在。

---

## 2026-01-17 14:14
**操作内容**: 收藏夹接口统一切换为 JWT 鉴权并移除 X-User-Id 依赖
**操作目标**: 取消 Header mock 鉴权，避免前端/测试误用 X-User-Id；收藏夹相关用例稳定通过
**操作结果**: 成功
**验证方式**:
- 运行 `uv run pytest test/src/test_auth_router.py test/src/test_collection_router.py test/src/test_collections_router.py`（33 passed）
**变更范围**:
- `main/backend/src/base/pg/service.py`
- `main/backend/src/service/agent/agent_state_service.py`
- `main/backend/test/src/test_collection_router.py`
- `main/backend/test/src/test_collections_router.py`
**备注**:
- 移除了 `get_current_user_id`（基于 `X-User-Id` 的 mock 鉴权），由路由侧统一使用 `get_current_user`（JWT）。
- 调整收藏夹路由相关测试：通过 dependency override 注入 `get_current_user`，不再在请求头中携带 `X-User-Id`。

---

## 2026-01-17 14:59
**操作内容**: 优化论文上传触发 Arq 任务时的 Redis 不可用处理
**操作目标**: Redis 未启动时不阻塞上传请求，避免长时间重试与超时日志刷屏
**操作结果**: 成功
**验证方式**:
- 运行 `python -m pytest`（exit code=0）
**变更范围**:
- `main/backend/src/service/papers/paper_service.py`
- `main/backend/test/src/test_paper_service_arq.py`
**备注**:
- 增加 TCP 级快速探测（短超时），Redis 不可达时直接跳过 enqueue。
- 单测通过 mock 探测逻辑，确保仍能覆盖 enqueue 与异常兜底路径。

---

## 2026-01-17 16:45
**操作内容**: 上传论文后自动加入默认收藏夹
**操作目标**: 用户未指定收藏夹上传时，论文可在默认收藏夹中被管理与查看
**操作结果**: 成功
**验证方式**:
- 运行 `python -m pytest -q`（exit code=0）
**变更范围**:
- `main/backend/src/service/papers/paper_service.py`
- `main/backend/test/src/test_paper_service.py`
- `main/backend/test/src/test_paper_service_arq.py`
**备注**:
- 逻辑：若默认收藏夹不存在则创建（并发下用 IntegrityError 回查兜底），随后写入 collection_papers 关联。
- 失败兜底：加入收藏夹失败只记录 warning，不影响上传主流程返回。

---

## 2026-01-17 16:57
**操作内容**: 论文上传支持指定收藏夹
**操作目标**: 上传时可通过 collection_id 将论文加入指定收藏夹，否则加入默认收藏夹
**操作结果**: 成功
**验证方式**:
- 运行 `python -m pytest -q`（exit code=0）
**变更范围**:
- `main/backend/src/controller/api/papers/router.py`
- `main/backend/src/service/papers/paper_service.py`
- `main/backend/test/src/test_papers_router.py`
- `main/backend/test/src/test_paper_service.py`
**备注**:
- upload 接口新增 multipart 字段 `collection_id`（可选），Service 层会先校验收藏夹归属。
- 指定收藏夹不存在/无权访问时返回 400，且不会落盘/入库。

---

## 2026-01-19 22:41
**操作内容**: 更新统一技术架构文档的数据库设计章节
**操作目标**: 基于当前后端实体与统一任务模型补齐数据库设计
**操作结果**: 成功
**验证方式**: 文档内容核对
**变更范围**:
- `PROJECT/DOCUMENTS/项目统一技术架构文档(重要).md`
**备注**:
- 增补统一 Job 模型、去重字段、版本化与补齐现有实体定义

---

## 2026-01-19 22:57
**操作内容**: 精简 Agent 相关数据库设计
**操作目标**: 仅保留 AgentSession，移除冗余字段说明
**操作结果**: 成功
**验证方式**: 文档内容核对
**变更范围**:
- `PROJECT/DOCUMENTS/项目统一技术架构文档(重要).md`
**备注**:
- 移除 ChatSession 中 thread_id 描述，Agent 仅保留 AgentSession 表
