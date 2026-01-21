# DeepResearcher - Agent持久化与用户配置设计方案

## 更新时间：2026-01-14 18:45

## 项目背景

本项目需要实现两个核心功能：
1. **Agent状态持久化 (T-142~T-144)**：支持Agent执行状态存储、中断恢复、人工介入等
2. **用户可配置项系统 (T-145~T-147)**：提供灵活的LLM参数、搜索设置、Agent行为、UI偏好等配置

## 设计方案概要

### 1. Agent持久化方案（LanggraphAgent设计）

#### 1.1 存储架构
采用LangGraph的checkpointer机制 + 自定义持久化服务的双轨存储架构：

```
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Checkpoint 机制                       │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   内存缓存   │  │  PostgreSQL  │  │     Redis        │  │
│  │  (运行时)   │  │  (持久化)    │  │   (可选缓存)     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│          ↓              ↓              ↓                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   LangGraph AsyncPOSTGressSaver (Checkpointer)    │   │
│  └─────────────────────────────────────────────────────┘   │
│                              ↓                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     EnhancedCheckpointSaver (自定义增强)            │   │
│  │  扩展checkpointer，管理interrupt和todo              │   │
│  └─────────────────────────────────────────────────────┘   │
│                              ↓                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    AgentPersistenceService                          │   │
│  │    统一管理Agent会话、中断、待办事项                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 核心实体设计

**(1) AgentSession - Agent会话**
```python
class AgentSession(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    user_id: UUID
    thread_id: str  # LangGraph线程ID
    agent_name: str  # Agent类型
    config: Dict  # 运行时配置
    status: str  # running, interrupted, completed, error
    created_at: datetime
    updated_at: datetime
```

**(2) AgentCheckpoint - 状态快照**
```python
class AgentCheckpoint(SQLModel, table=True):
    thread_id: str
    checkpoint_id: str
    parent_id: Optional[str]
    checkpoint: Dict  # 序列化状态
    metadata: Dict
    created_at: datetime
```

**(3) AgentTodo - 待办事项**
```python
class AgentTodo(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    session_id: UUID
    todo_type: str  # approval, input, selection
    message: str
    data: Dict  # 附加数据
    status: str  # pending, completed
    result: Optional[Dict]
    created_at: datetime
    completed_at: Optional[datetime]
```

#### 1.3 中断恢复机制

**强中断（Immediate Interrupt）**
- Agent在关键节点调用 `interrupt()` 暂停
- 状态自动保存到checkpoint
- 前端显示弹窗获取用户输入
- 使用 `Command(resume=...)` 恢复执行

**弱中断（Todo Pipeline）**
- Agent创建待办事项并继续执行
- 用户通过待办列表异步处理
- 所有待办完成后自动恢复

#### 1.4 前端交互流程

**中断处理：**
```
Agent执行 → 触发中断 → 保存状态 → SSE推送中断事件 →
前端弹窗 → 用户输入 → POST恢复接口 → 命令恢复 → 继续执行
```

**待办处理：**
```
Agent执行 → 创建待办 → SSE推送待办事件 →
前端通知 → 用户处理 → POST完成接口 → 检查状态 → 自动恢复
```

#### 1.5 关键API设计

```typescript
// 获取会话状态
GET /agent/sessions/{session_id}/state

// 恢复中断的会话
POST /agent/sessions/{thread_id}/restore
{
  "resume_data": { "user_input": "..." }
}

// 获取待办列表
GET /agent/sessions/{session_id}/todos

// 完成待办
POST /agent/todos/{todo_id}/complete
{
  "result_data": { "approved": true }
}
```

---

### 2. 用户可配置项系统（BackendAgent设计）

#### 2.1 配置层级
采用三级配置策略：
- **系统级**：管理员配置，全局生效（LLM模型、搜索服务）
- **用户级**：用户偏好，仅对当前用户生效（UI主题、阅读偏好、Agent行为）
- **会话级**：临时设置，仅当前会话有效

#### 2.2 数据库设计

```sql
-- 配置分类表
CREATE TABLE config_categories (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    name VARCHAR(100),
    description TEXT
);

-- 配置项定义表
CREATE TABLE config_definitions (
    id UUID PRIMARY KEY,
    category_id UUID REFERENCES config_categories,
    key VARCHAR(200) NOT NULL,
    name VARCHAR(200),
    description TEXT,
    value_type VARCHAR(50),
    default_value JSONB,
    validation_rules JSONB,
    options JSONB,
    scope VARCHAR(50),  -- system/user/session
    is_public BOOLEAN,
    UNIQUE(category_id, key)
);

-- 用户配置值表
CREATE TABLE user_config_values (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    config_id UUID REFERENCES config_definitions,
    value JSONB NOT NULL,
    UNIQUE(user_id, config_id)
);
```

#### 2.3 配置项分类

**系统级配置：**
- LLM模型选择（gpt-4, claude等）
- 模型参数（temperature, max_tokens）
- 搜索服务权重（Google Scholar: 0.4, ArXiv: 0.3）
- 超时时间

**用户级配置：**
- 界面偏好（主题、语言、字体大小）
- 阅读偏好（PDF阅读器模式、缩放、高亮颜色）
- Agent行为（搜索深度、摘要长度、对话风格）

**Agent专属配置：**
- SearchAgent：混合搜索权重、相关性阈值
- SummaryAgent：摘要长度、关键信息提取规则
- DeepResearchAgent：最大迭代次数、研究深度

#### 2.4 配置服务架构

```python
class ConfigProvider:
    """为Agent提供配置数据"""
    async def get_agent_config(self, user_id: str, agent_name: str) -> Dict:
        # 获取Agent专属配置，支持分层覆盖
        pass

class UserSettingsService:
    """管理用户配置"""
    async def get_user_settings(self, user_id: str) -> Dict:
        pass

    async def update_user_settings(
        self, user_id: str, settings: Dict
    ) -> Dict:
        pass
```

#### 2.5 API设计

```typescript
// 获取用户配置
GET /api/v1/users/settings

// 获取Agent配置
GET /api/v1/agents/{agent_name}/config

// 更新配置
PUT /api/v1/users/settings/{key}
{
  "value": "dark"
}

// 批量更新
PUT /api/v1/users/settings/batch
{
  "theme": "dark",
  "language": "en",
  "search.depth": 5
}
```

#### 2.6 缓存策略

三级缓存架构：
- **内存缓存**：热点配置（LRU，容量控制）
- **Redis缓存**：用户配置（TTL: 1小时）
- **PostgreSQL**：持久化存储

#### 2.7 版本管理

```python
class ConfigMigration:
    """配置迁移管理"""
    async def migrate(
        self, user_id: str, from_version: str, to_version: str
    ):
        # 执行配置迁移脚本
        pass
```

---

### 3. 前后端集成方案

#### 3.1 前端状态管理

```typescript
// Agent状态管理
interface AgentState {
  sessionId?: string;
  threadId?: string;
  interruptInfo?: InterruptInfo;
  todos: TodoItem[];
  config: AgentConfig;
}

// 配置管理
interface AgentConfig {
  llmModel: string;
  temperature: number;
  searchDepth: number;
  maxResults: number;
  // ... 其他配置
}
```

#### 3.2 SSE事件处理

```typescript
// 统一SSE事件处理
const handleSSEvent = (event: MessageEvent) => {
  const data = JSON.parse(event.data);

  switch (data.event) {
    case 'interrupt':
      // 处理中断事件
      showInterruptModal(data.data);
      break;

    case 'todo':
      // 处理待办事件
      addTodo(data.data);
      break;

    case 'config_updated':
      // 处理配置更新
      updateConfig(data.data);
      break;

    default:
      // 处理其他事件（token、tool等）
      handleChatEvent(data);
  }
};
```

#### 3.3 React Hooks封装

```typescript
// Agent会话管理Hook
const useAgentSession = (agentName: string) => {
  const [session, setSession] = useState<AgentSession | null>(null);
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [interruptInfo, setInterruptInfo] = useState<InterruptInfo | null>(null);

  // 发送消息
  const sendMessage = async (message: string) => {
    // 发送消息并处理SSE
  };

  // 处理待办
  const completeTodo = async (todoId: string, result: any) => {
    await api.post(`/agent/todos/${todoId}/complete`, { result_data: result });
  };

  // 恢复中断
  const resumeInterrupt = async (userInput: any) => {
    await api.post(`/agent/sessions/${threadId}/restore`, {
      resume_data: { user_input: userInput }
    });
  };

  return { session, todos, interruptInfo, sendMessage, completeTodo, resumeInterrupt };
};

// 配置管理Hook
const useAgentConfig = (agentName: string) => {
  const [config, setConfig] = useState<AgentConfig | null>(null);

  const updateConfig = async (updates: Partial<AgentConfig>) => {
    await api.put(`/api/v1/users/settings/batch`, updates);
    // 触发重新加载
  };

  return { config, updateConfig };
};
```

---

### 4. 实施计划

#### 4.1 第一阶段（第1-2天）

**BackendAgent任务：**
1. 创建用户配置数据库表
2. 实现配置服务基础功能（ConfigProvider, UserSettingsService）
3. 实现配置缓存（Redis + 内存缓存）
4. 编写配置单元测试

**LanggraphAgent任务：**
1. 完善Agent持久化实体定义
2. 实现EnhancedCheckpointSaver
3. 实现AgentPersistenceService
4. 集成AsyncPostgresSaver

#### 4.2 第二阶段（第3-4天）

**BackendAgent任务：**
1. 实现RESTful API接口（用户设置、Agent配置）
2. 添加权限控制和验证
3. 实现配置版本管理
4. 编写API集成测试

**LanggraphAgent任务：**
1. 实现Agent会话管理API
2. 实现中断恢复API
3. 实现待办事项管理API
4. 集成到现有Agent中

#### 4.3 第三阶段（第5天）

**BackendAgent任务：**
1. 与LanggraphAgent进行配置集成
2. 实现配置热更新机制
3. 性能优化和缓存调优

**LanggraphAgent任务：**
1. 在Agent状态中添加config字段
2. 实现配置读取逻辑
3. 测试中断恢复功能

#### 4.4 第四阶段（第6-7天）

**FrontendAgent任务：**
1. 实现配置管理页面
2. 实现中断处理组件（InterruptModal）
3. 实现待办事项组件（TodoList）
4. 封装React Hooks（useAgentSession, useAgentConfig）
5. 集成到现有聊天界面

**集成测试：**
1. 端到端测试配置流程
2. 端到端测试中断恢复流程
3. 压力测试
4. 性能基准测试

---

### 5. 关键里程碑

| 里程碑 | 交付物 | 预计完成时间 | 状态 |
|--------|--------|--------------|------|
| M1：数据库设计 | 完整的表结构、索引、关系 | 2026-01-15 | 🟢 已完成设计 |
| M2：后端服务 | ConfigProvider、AgentPersistenceService | 2026-01-17 | 🟡 进行中 |
| M3：RESTful API | 完整的API接口和文档 | 2026-01-18 | 🔴 待开始 |
| M4：Agent集成 | Agent读取配置、支持中断 | 2026-01-19 | 🔴 待开始 |
| M5：前端组件 | 配置页面、中断组件、Hooks | 2026-01-21 | 🔴 待开始 |
| M6：端到端测试 | 完整的功能测试报告 | 2026-01-22 | 🔴 待开始 |

---

### 6. 风险评估与应对

#### 6.1 技术风险

**风险1：LangGraph异步持久化性能问题**
- 概率：中
- 影响：高
- 应对：提前进行性能测试，准备Redis缓存方案，使用批量操作

**风险2：配置数据结构变更导致的兼容性问题**
- 概率：中
- 影响：中
- 应对：实施严格的版本管理，提供配置迁移工具，单元测试覆盖

**风险3：前端状态管理的复杂性**
- 概率：低
- 影响：中
- 应对：使用成熟的React状态管理库（Zustand或Redux），封装可复用的Hooks

#### 6.2 进度风险

**风险：两个Agent并行开发导致的接口不匹配**
- 概率：中
- 影响：中
- 应对：定期进行接口评审，使用OpenAPI/Swagger定义接口契约，提前进行集成测试

---

### 7. 验收标准

#### 7.1 Agent持久化验收

- ✅ 状态持久化：Agent每次节点执行后状态正确保存
- ✅ 中断恢复：强中断后能精确恢复到中断点
- ✅ 待办管理：弱中断创建的待办能正确显示和处理
- ✅ 前端集成：中断弹窗和待办列表正常工作
- ✅ 性能：状态保存和恢复时间 < 100ms
- ✅ 稳定性：1000次连续中断恢复操作无错误

#### 7.2 用户配置验收

- ✅ 配置CRUD：支持所有配置项的创建、读取、更新、删除
- ✅ 分层覆盖：系统 → 用户 → 会话的正确覆盖逻辑
- ✅ Agent集成：Agent能正确读取和使用配置
- ✅ 热更新：配置变更实时生效，无需重启
- ✅ 版本管理：支持配置版本升级和回滚
- ✅ 缓存性能：配置读取时间 < 50ms（缓存命中）

---

### 8. 相关文档

- **BackendAgent设计**：`AGENT/BackendAgent/DESIGN_USER_CONFIG.md`
- **LanggraphAgent设计**：`AGENT/LangGraphAgent/AGENT_PERSISTENCE_DESIGN.md`
- **技术架构**：`PROJECT/TECHNICAL_ARCHITECTURE.md`
- **前端API需求**：`PROJECT/DOCUMENTS/FRONTEND_TO_BACKEND_API_REQ.md`

---

### 9. 附录

#### 9.1 配置文件示例

**系统配置（system-level）：**
```json
{
  "llm": {
    "default_model": "gpt-4-turbo",
    "fallback_model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "search": {
    "services": {
      "google_scholar": { "weight": 0.4, "timeout": 30 },
      "arxiv": { "weight": 0.3, "timeout": 30 },
      "pubmed": { "weight": 0.3, "timeout": 30 }
    },
    "max_results": 50
  }
}
```

**用户配置（user-level）：**
```json
{
  "ui": {
    "theme": "dark",
    "language": "zh",
    "font_size": "16px"
  },
  "reading": {
    "pdf_reader_mode": "scroll",
    "default_zoom": "fit_width",
    "highlight_color": "#FFEB3B"
  },
  "agent_behavior": {
    "search_depth": 3,
    "summary_length": "medium",
    "conversation_style": "detailed"
  },
  "search_enhancement": {
    "mix_search_weights": {
      "dense": 0.4,
      "sparse": 0.3,
      "bm25": 0.3
    },
    "relevance_threshold": 0.7
  }
}
```

#### 9.2 前端组件清单

| 组件 | 文件路径 | 描述 |
|------|----------|------|
| InterruptModal | `components/agent/InterruptModal.tsx` | 中断处理弹窗 |
| TodoList | `components/agent/TodoList.tsx` | 待办事项列表 |
| TodoCard | `components/agent/TodoCard.tsx` | 待办卡片 |
| SessionStateRecovery | `components/agent/SessionStateRecovery.tsx` | 会话恢复 |
| AgentConfigPanel | `components/settings/AgentConfigPanel.tsx` | Agent配置面板 |
| useAgentSession | `hooks/useAgentSession.ts` | Agent会话Hook |
| useAgentConfig | `hooks/useAgentConfig.ts` | Agent配置Hook |

---

**文档维护者**：MasterAgent
**最后更新**：2026-01-14 18:45
**版本**：v1.0
