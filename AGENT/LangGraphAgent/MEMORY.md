# Agent 记忆: LangGraphAgent

## 1. 最小项目概念与模块关系
- **角色**: LangGraph Agent 研发与编排。
- **范围**: `/main/backend/src/agent/` (Agent 层)。
- **核心依赖**: LangGraph 1.0+, LangChain 1.1.0+, `deepagents` (LangChain Team 新库)。
- **已开发模块**:
  - **DeepResearchAgent**: 基于 `deepagents` 库实现的深度研究 Agent，集成 Arxiv 搜索能力。
- **交互**: 
  - 输入: 用户请求 / 系统触发。
  - 过程: 图执行 -> 节点处理 -> 工具使用。
  - 输出: 流式事件 / 状态更新。

## 2. 关键纠正与反思
- **架构迁移**: 从手动构建 `StateGraph` 转向使用 `deepagents.create_deep_agent`。这简化了编排，但要求对内部机制（如 Middleware）有更深理解。
- **逻辑集成 (Zombie Code)**: 在使用预构建 Agent 架构时，原 `node.py` 中的业务逻辑（如规划、报告生成）如果不能作为图节点直接插入，必须转化为 **Tools** 供 Agent 调用，否则会成为无法访问的僵尸代码。
- **异步规范**: Agent 运行在异步事件循环中，Tools 内部严禁使用阻塞式 IO (如 `urllib`)，必须使用异步库 (如 `httpx`)，否则会卡死整个 Agent 的并发处理。
- **提交规范**: 提交代码时 (`SUBMISSION`) 必须保持与 `SANDBOX` 一致的目录层级，并包含所有相关文件，不能只提交修改片段。

## 3. 自我理解与核心代码抽象
- **DeepAgent 模式**:
  ```python
  from deepagents import create_deep_agent
  agent = create_deep_agent(tools=[...], system_prompt=...)
  ```
- **业务逻辑工具化**: 将“思考-执行”链条中的复杂确定性逻辑（如生成固定格式报告）封装为 Tool，而非 Graph Node，以便于大模型灵活调度。
- **异步工具模式**:
  ```python
  @tool
  async def async_tool(arg: str):
      async with httpx.AsyncClient() as client:
          resp = await client.get(...)
          return resp
  ```
