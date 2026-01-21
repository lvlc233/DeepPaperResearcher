# 前端对接后端 API 需求说明书 (Frontend to Backend API Requirements)

> **版本**: v1.0
> **日期**: 2026-01-11
> **提交方**: FrontendAgent
> **说明**: 本文档基于前端已实现的 UI 组件及业务逻辑 (`ReaderRightPanel`, `PDFPageOverlay`, `ChatBox` 等) 整理而成，旨在向后端明确具体的数据交互需求、接口定义及 SSE 协议细节。

---



---

## 2. 论文管理模块 (Papers)

支持论文上传、列表展示及状态轮询。

### 2.1 接口列表
| Method | Path | Description | Payload/Params | Response |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/papers/upload` | 上传论文 | `FormData { file: File }` | `{id, title, status: 'processing'}` |
| `GET` | `/api/v1/papers` | 获取论文列表 | `?page=1&limit=20&sort=created_at` | `{items: Paper[], total}` |
| `GET` | `/api/v1/papers/{id}` | 获取论文详情 | - | `Paper & { status, file_url, authors, abstract }` |
| `GET` | `/api/v1/papers/{id}/status` | 轮询解析状态 | - | `{status: 'pending'|'processing'|'completed'|'failed', progress: 0-100}` |
| `DELETE` | `/api/v1/papers/{id}` | 删除论文 | - | `{success: true}` |

---

## 3. 阅读器核心交互 (Reader Core)

支持 PDF 阅读过程中的图层管理、标注同步及辅助功能。

### 3.1 图层与标注 (Layers & Annotations)
前端采用 "View as Layer" 架构，需要后端持久化存储图层及标注数据。

#### 数据结构参考
```typescript
interface Annotation {
  id: string;
  type: 'highlight' | 'note' | 'translate';
  rects: {x, y, width, height, pageIndex}[]; // 百分比坐标
  content?: string;
  color?: string;
  createdAt: number;
}

interface Layer {
  id: string;
  name: string; // e.g., "我的高亮", "AI 自动标注"
  type: 'system' | 'user';
  visible: boolean;
  annotations: Annotation[];
}
```

#### 接口列表
| Method | Path | Description | Payload/Params | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/papers/{id}/layers` | 获取某篇论文的所有图层 | - | `{layers: Layer[]}` |
| `POST` | `/api/v1/papers/{id}/layers` | 创建新图层 | `{name, type}` | `{id, name, ...}` |
| `POST` | `/api/v1/layers/{layerId}/annotations` | 添加标注 | `Annotation` (without id) | `Annotation` (with id) |
| `PUT` | `/api/v1/annotations/{annoId}` | 更新标注 (颜色/笔记内容) | `{color?, content?}` | `Annotation` |
| `DELETE` | `/api/v1/annotations/{annoId}` | 删除标注 | - | `{success: true}` |

### 3.2 辅助功能 (Auxiliary Features)
对应 `ReaderRightPanel` 中的各个 Tab。

#### 3.2.1 导读 (Guide Tab)
| Method | Path | Description | Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/papers/{id}/summary` | 获取论文结构化导读 | - | `{summary: string, key_points: string[]}` |
| `POST` | `/api/v1/papers/{id}/generate-summary` | 触发导读生成 (如未生成) | - | `{status: 'generating'}` (SSE or Async) |

#### 3.2.2 脑图 (Graph Tab)
前端使用 `reagraph`，需要节点和边的数据。
| Method | Path | Description | Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/papers/{id}/graph` | 获取知识图谱数据 | - | `{nodes: GraphNode[], edges: GraphEdge[]}` |

#### 3.2.3 报告 (Report Tab)
支持生成深度研究报告。
| Method | Path | Description | Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/papers/{id}/reports` | 获取报告列表 | - | `{reports: ReportItem[]}` |
| `POST` | `/api/v1/papers/{id}/reports` | 创建生成任务 | `{type: 'deep_research'|'related_work'}` | `{reportId, status: 'generating'}` |
| `GET` | `/api/v1/reports/{reportId}` | 获取报告详情 | - | `ReportItem` |

---

## 4. 统一对话服务 (Unified Chat Service)

支持多 Agent 路由 (Search, Chat, DeepResearch) 及流式响应。

### 4.1 会话管理
| Method | Path | Description | Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/chat/sessions` | 创建会话 | `{agent_type: 'chat'|'search', context: {paperId?}}` | `{sessionId, title, created_at}` |
| `GET` | `/api/v1/chat/sessions` | 获取会话列表 | `?limit=20` | `{sessions: ChatSession[]}` |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | 获取历史消息 | - | `{messages: ChatMessage[]}` |

### 4.2 SSE 交互协议 (SSE Protocol)
前端 `use-unified-chat` 钩子期望的事件流格式。后端需确保 `text/event-stream` 响应符合以下规范。

**Endpoint**: `POST /api/v1/chat/sessions/{sessionId}/message`

**Request Body**:
```json
{
  "content": "用户输入的问题",
  "files": [] // 可选，上传的附件
}
```

**Event Types**:

1.  **`metadata`** (连接建立时发送)
    ```json
    data: {"run_id": "uuid", "session_id": "uuid", "agent_name": "InPaperChatAgent"}
    ```

2.  **`token`** (流式文本输出)
    ```json
    data: "这是"
    data: "一段"
    data: "回复"
    ```

3.  **`tool_call`** (工具调用开始 - 用于前端展示 Loading 状态)
    ```json
    data: {
      "tool_name": "search_local_papers",
      "args": {"query": "transformer attention"},
      "status": "start"
    }
    ```

4.  **`tool_result`** (工具调用结束 - 用于前端展示中间结果)
    ```json
    data: {
      "tool_name": "search_local_papers",
      "result": "Found 3 papers...",
      "status": "success"
    }
    ```

5.  **`citation`** (引用来源 - 必须字段)
    ```json
    data: {
      "source_id": "paper_uuid",
      "chunk_id": "chunk_uuid",
      "text": "原文片段...",
      "score": 0.89
    }
    ```

6.  **`finish`** (结束信号)
    ```json
    data: {"reason": "stop", "usage": {"prompt_tokens": 100, "completion_tokens": 50}}
    ```

7.  **`error`** (异常处理)
    ```json
    data: {"code": 500, "message": "Vector store connection failed"}
    ```

---

## 5. 数据类型定义 (Type Definitions)

为了确保前后端契合，请参考以下 TypeScript 定义生成 Pydantic 模型。

### 5.1 GraphNode (用于知识图谱)
```typescript
interface GraphNode {
  id: string;
  label: string;
  fill?: string; // 节点颜色
  size?: number;
  data?: {
    type: 'concept' | 'paper' | 'author';
    description?: string;
  };
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string; // 关系名称
}
```

### 5.2 ReportItem (用于报告)
```typescript
interface ReportItem {
  id: string;
  title: string;
  createTime: string; // ISO 8601
  status: 'completed' | 'generating' | 'failed' | 'cancelled';
  content: string; // Markdown 格式
  summary?: string;
}
```
(感觉可以合并到统一架构文案中。)