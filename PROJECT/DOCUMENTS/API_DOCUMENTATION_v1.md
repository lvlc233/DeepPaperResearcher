# DeepPaperResearcher API 文档 (v0.2 实现版)

> **版本**: v0.2
> **状态**: 已实现 (Implemented)
> **基准 URL**: `http://localhost:8000/api/v1`
> **说明**: 本文档基于后端实际代码生成，用于前端对接联测。

## 1. 认证与用户 (Auth & Users)

### 1.1 登录
- **URL**: `/auth/login`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "code": 200,
    "message": "Success",
    "data": {
      "access_token": "eyJhbG...",
      "token_type": "bearer",
      "user": { ... }
    }
  }
  ```

### 1.2 注册
- **URL**: `/auth/register`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }
  ```

TODO: 修改密码:(后面再说p5)

### 1.3 获取当前用户
- **URL**: `/users/me`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <token>`

### 1.4 更新用户设置(p3)
- **URL**: `/users/settings`
- **Method**: `PUT`
- **Body**:
  ```json
  {
    "settings": {
      "theme": "dark",
      "language": "zh"
    }
  }
  ```

---

## 2. 论文管理 (Papers)

### 2.1 获取论文列表
- **URL**: `/papers/list`  *(注意：非 `/papers`)*
- **Method**: `GET`
- **Query Params**:
  - `limit`: int (default 10)
  - `offset`: int (default 0)
- **Response**: `[ { "id": "...", "title": "...", "status": "..." } ]`

### 2.2 上传论文 (PDF)
- **URL**: `/papers/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: File (PDF)
- **Response**: `{ "id": "...", "status": "pending" }`

### 2.3 通过 URL 获取论文 (ArXiv)
- **URL**: `/papers/fetch`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "url": "https://arxiv.org/abs/1706.03762",
    "source": "arXiv"
  }
  ```
- **Response**: 返回解析后的论文元数据列表。

### 2.4 获取论文状态详情
- **URL**: `/papers/{paper_id}/status`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "paper_id": "...",
    "status": "completed",
    "progress": 100,
    "toc": [ ... ],
    "file_url": "..."
  }
  ```

### 2.5 触发论文解析 (手动)
- **URL**: `/papers/{paper_id}/process`
- **Method**: `POST`
- **Response**: `{ "status": "accepted" }`

---

## 3. 阅读器 (Reader)

### 3.1 摘要 (Summary)
- **获取**: `GET /reader/papers/{paper_id}/summary?summary_type=default`
- **生成**: `POST /reader/papers/{paper_id}/summary`
  ```json
  { "content": "...", "summary_type": "default" }
  ```

### 3.2 图层 (Layers)
- **列表**: `GET /reader/papers/{paper_id}/layers`
- **创建**: `POST /reader/papers/{paper_id}/layers`
- **更新**: `PUT /reader/layers/{layer_id}`
- **删除**: `DELETE /reader/layers/{layer_id}`

### 3.3 标注 (Annotations)
- **创建**: `POST /reader/layers/{layer_id}/annotations`
- **更新**: `PUT /reader/annotations/{anno_id}`
- **删除**: `DELETE /reader/annotations/{anno_id}`

### 3.4 笔记 (Notes)
- **列表**: `GET /reader/papers/{paper_id}/notes`
- **创建**: `POST /reader/papers/{paper_id}/notes`
- **更新**: `PUT /reader/notes/{note_id}`
- **删除**: `DELETE /reader/notes/{note_id}`

### 3.5 思维导图 (Mind Map)
- **获取**: `GET /reader/papers/{paper_id}/graph`
- **更新**: `PUT /reader/papers/{paper_id}/graph`

---

## 4. 收藏夹 (Collections)

- **列表**: `GET /collections`
- **创建**: `POST /collections`
- **详情**: `GET /collections/{id}` (包含论文列表)
- **更新**: `PUT /collections/{id}`
- **删除**: `DELETE /collections/{id}`
- **添加论文**: `POST /collections/{id}/papers` (`{ "paper_id": "..." }`)
- **移除论文**: `DELETE /collections/{id}/papers/{paper_id}`

---

## 5. 搜索 (Search)

### 5.1 搜索论文
- **URL**: `/search`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "query": "transformer",
    "page": 1,
    "page_size": 10,
    "filters": { "year_start": 2020 }
  }
  ```

### 5.2 搜索历史
- **获取**: `GET /search/history`
- **清空**: `DELETE /search/history`

### 5.3 搜索配置
- **获取**: `GET /search/config`
- **更新**: `PUT /search/config`

---

## 6. 聊天 (Chat) & SSE

### 6.1 会话管理
- **创建**: `POST /chat/sessions` (`{ "agent_type": "paper_chat", "context": { "paper_id": "..." } }`)
- **列表**: `GET /chat/sessions`
- **详情**: `GET /chat/sessions/{id}`
- **历史消息**: `GET /chat/sessions/{id}/messages`

### 6.2 发送消息 (SSE 流式)
- **URL**: `/chat/sessions/{session_id}/message`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Body**: `{"content": "解释一下Attention机制"}`
- **Response**: `text/event-stream`

**SSE 事件类型**:
1. `metadata`: `{"run_id": "...", "session_id": "..."}`
2. `token`: `{"content": "..."}` (注意: 实际代码目前直接返回字符串 token，请以前端适配为准，代码逻辑是 `json.dumps(content)`)
3. `error`: `{"error": "..."}`
4. `finish`: `{"reason": "stop"}`

---

## 7. 报告 (Reports) [Mock]
> 注意：此模块目前仅返回模拟数据。

- **列表**: `GET /reports/papers/{paper_id}/reports`
- **创建**: `POST /reports/papers/{paper_id}/reports`
- **详情**: `GET /reports/reports/{report_id}`
(感觉可以合并到统一架构文案中。)