# 前端项目实现规范文档

**文档信息**
- **负责人**: FrontendAgent
- **日期**: 2026-01-06
- **版本**: v1.0
- **关联任务**: T-008

---

## 1. 工程架构

### 1.1 目录结构
采用 Next.js App Router 推荐的模块化结构，强调“高内聚”。

```text
src/
├── app/                    # 路由层 (Pages & Layouts)
│   ├── (auth)/             # 鉴权相关 (登录/注册)
│   ├── (dashboard)/        # 主业务区 (需登录)
│   │   ├── layout.tsx      # Dashboard 布局 (侧边栏 + 顶栏)
│   │   ├── library/        # 论文库管理
│   │   ├── graph/          # 知识图谱
│   │   └── reader/[id]/    # 论文阅读器
│   ├── api/                # 后端 API 转发层 (BFF)
│   ├── globals.css         # 全局样式
│   └── layout.tsx          # 根布局
├── components/             # 组件层
│   ├── ui/                 # 基础 UI 组件 (Shadcn/UI, 无业务逻辑)
│   ├── business/           # 业务组件 (复用性强, 如 PdfViewer, GraphCanvas)
│   ├── layout/             # 布局组件 (Sidebar, Header)
│   └── providers/          # 全局 Context Providers (QueryClient, Theme)
├── hooks/                  # 自定义 Hooks (use-pdf-view, use-ai-chat)
├── lib/                    # 工具库
│   ├── api/                # API 客户端封装 (Axios + Interceptors)
│   ├── utils.ts            # 通用工具函数 (cn, formatters)
│   └── constants.ts        # 常量定义
├── services/               # 业务服务层 (API 定义)
│   ├── auth.service.ts
│   ├── paper.service.ts
│   └── ai.service.ts
├── store/                  # 全局状态 (Zustand)
│   ├── use-app-store.ts    # UI 状态 (Sidebar toggle, etc.)
│   └── use-reader-store.ts # 阅读器状态 (Current Page, View Layers)
└── types/                  # TypeScript 类型定义
    ├── api.d.ts            # 接口响应类型
    ├── models.d.ts         # 业务实体模型
    └── index.d.ts          # 全局类型
```

### 1.2 状态管理策略
遵循“由近及远”原则：
1.  **Component State**: `useState` / `useReducer` (仅组件内部使用，如表单输入)。
2.  **Server State**: `TanStack Query` (所有 API 数据，禁止存入 Redux/Zustand)。
3.  **URL State**: 将筛选条件、分页参数、当前视图 ID 同步到 URL Query Params (便于分享和后退)。
4.  **Global Client State**: `Zustand` (仅用于跨组件 UI 状态，如阅读器设置、全局弹窗)。

---

## 2. 编码规范

### 2.1 TypeScript 规范
*   **Strict Mode**: 必须开启 `strict: true`。
*   **No Any**: 严禁使用 `any`。如遇未知类型，使用 `unknown` 并配合类型守卫。
*   **Interfaces**: 优先使用 `interface` 定义对象结构，`type` 定义联合类型。
*   **Props**: 组件 Props 必须定义类型，推荐使用 `FC<Props>` 或直接解构 `{ prop }: Props`。

### 2.2 组件规范
*   **函数组件**: 统一使用 Function Declaration (`export function MyComponent() {}`)。
*   **副作用**: 所有副作用收敛到 `useEffect` 或 Event Handlers。
*   **Memoization**:
    *   对于传递给子组件的回调函数，必须使用 `useCallback`。
    *   对于复杂计算 (如 PDF 坐标转换、图谱数据处理)，必须使用 `useMemo`。
*   **Server Components (RSC)**:
    *   默认编写 RSC (无 `'use client'`)。
    *   仅在需要交互 (onClick, useState) 时添加 `'use client'` 指令，并尽量下沉到叶子组件。

### 2.3 样式规范
*   **TailwindCSS**: 优先使用 Utility Classes。
*   **clsx / twMerge**: 使用 `cn()` 工具函数合并类名，避免样式冲突。
*   **CSS Modules**: 仅在 Tailwind 无法满足的极其复杂动画或伪类场景下使用。

### 2.4 注释规范
所有导出的函数、组件、Hook 必须包含 JSDoc 注释：
```typescript
/**
 * PDF 阅读器组件
 * 
 * 负责渲染 PDF 页面及叠加自定义视图层 (Annotation Layer)。
 * 
 * @param {string} url - PDF 文件地址
 * @param {string} initialPage - 初始页码
 * @returns {JSX.Element}
 */
```

---

## 3. 核心功能实现指南

### 3.1 PDF 视图层 (The View Layer)
*   **概念**: 视图 (View) 是覆盖在 PDF 原文上的一层透明 SVG/Canvas。
*   **实现**:
    1.  使用 `react-pdf` 渲染底图 (Canvas)。
    2.  在其上方绝对定位一个 `div` (z-index: 10)，尺寸与 PDF Page 一致。
    3.  在该 `div` 内渲染 SVG 元素表示高亮、划线。
    4.  **坐标系**: 所有坐标存储为百分比 (0.0 - 1.0)，渲染时乘以当前容器宽高，确保缩放自适应。

### 3.2 AI 流式交互
*   **SDK**: 使用 Vercel AI SDK (`ai/react`)。
*   **Hooks**: `useChat` 用于对话，`useCompletion` 用于单次生成。
*   **Data Stream**: 利用 `data` 字段处理中间状态。
    ```typescript
    // 前端处理逻辑示例
    const { messages, data } = useChat();
    // data 包含: [{ type: 'tool', status: 'searching', query: '...' }]
    ```

### 3.3 知识图谱
*   **库**: `reagraph`。
*   **交互**:
    *   **点击**: 导航至对应论文。
    *   **Lasso (套索)**: 触发批量操作 (如 "Deep Research Selected")。
    *   **节点渲染**: 根据节点类型 (`paper`, `author`, `concept`) 渲染不同颜色/形状。

---

## 4. 协作与版本控制

### 4.1 Git 提交规范
格式: `type(scope): subject`
*   `feat`: 新功能
*   `fix`: 修复 Bug
*   `docs`: 文档变更
*   `style`: 代码格式调整 (不影响逻辑)
*   `refactor`: 重构
*   `perf`: 性能优化
*   `chore`: 构建/工具链变动

### 4.2 开发流程
1.  领取任务 (Task ID)。
2.  创建分支 (如 `feat/reader-view`)。
3.  开发并自测 (Lint, Type Check)。
4.  提交代码并记录操作日志。
5.  合并至主分支。

---

## 5. 错误处理与监控
*   **API 错误**: 在 `axios` 拦截器中统一处理 (如 401 跳转登录, 500 提示 Toast)。
*   **UI 错误**: 使用 `react-error-boundary` 包裹核心模块 (如 PDF Viewer)，防止局部崩溃导致白屏。
*   **日志**: 关键操作调用 `logger.info/error` (仅在开发环境输出到 Console，生产环境可接入监控)。
