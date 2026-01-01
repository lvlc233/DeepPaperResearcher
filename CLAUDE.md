# CLAUDE.md

本文档用于指导 Claude Code（claude.ai/code）在本仓库中开展开发工作。

## 项目概览

DeepResearcher 是一个基于 LangGraph 构建、AI 辅助的论文研究与管理平台。项目采用严格的“3+1”层架构，并区分 AGENT 与 SUBMISSION 两条工作流进行迭代开发。

## 开发命令

### 后端开发
```bash
# 进入后端目录
cd main/backend

# 安装依赖（使用 uv）
uv add fastapi langchain langgraph sqlmodel psycopg2-binary redis neo4j pyjwt

# 启动后端（待 main.py 创建后）
uv run python main.py

# 运行测试
uv run pytest test/src/      # 单元测试
uv run pytest test/agent/    # Agent 测试

# 单测指定用例
uv run pytest test/src/path/to/test.py::test_function_name -v
```

### 代码质量
```bash
# 格式化（如已配置）
uv run ruff format .
uv run ruff check .

# 类型检查（如已配置）
uv run mypy src/
```

## 架构与关键模式

### 后端“3+1”层架构
- **Controller 层**（`src/controller/`）：FastAPI 路由、请求/响应模型、认证鉴权
- **Service 层**（`src/service/`）：业务逻辑、数据合成、基础设施编排
- **Infrastructure 层**（`src/base/`）：数据库操作（PostgreSQL via SQLModel、Redis、Neo4j）
- **Data 层**（`src/business_model/`）：纯 Pydantic 模型，不含业务逻辑

### Agent 开发模式
每个 Agent 都是一个编译后的 LangGraph，包含：
- **State**（`schema.py`）：TypedDict，必须含 `messages` 与 `context` 字段
- **Nodes**（`node.py`）：独立处理单元，返回 dict 更新
- **Tools**（`tools.py`）：函数单元，需完善异常处理
- **Router**（`agent.py`）：条件逻辑，控制节点跳转

Agent 开发守则：
- State 用 TypeDict，不用 dataclass/BaseModel
- Messages 必须使用 langchain 的 Message 类
- 所有工具必须捕获异常并更新 context
- 工具内用 Command 回写状态
- 同时支持强（中断）与弱（管道）人工干预

### 代码规范
每个模块须包含：
```python
'''
开发者: agent_name/human_name
当前版本: unique_version_string
创建时间: YYYY-MM-DD
更新时间: YYYY-MM-DD
更新记录:
    [YYYY-MM-DD:version:brief_description]
'''
```

### 开发工作流
1. **AGENT/**：个人工作区，含 MEMORY、OPERATION_LOG、SANDBOX
2. **SUBMISSION/**：代码提交区，用于评审
3. **PROJECT/**：核心规格文档（普通 Agent 只读）

### 测试要求
Agent 必须三级测试：
1. **单元测试**：mock 节点/工具的输入输出
2. **模型测试**：真实 LLM 调用，多上下文验证（使用 langfuse）
3. **集成测试**：端到端真实数据（需构造数据集）

## 重要约束
- 禁止使用假数据——未实现逻辑用 TODO 注释
- 所有功能必须通过测试方可交付
- 时间戳统一采用上海（中国）时区
- 代码注释须使用中文
- Controller 禁止直接访问数据库，须走 Service 层
- 所有数据模型必须显式声明返回类型