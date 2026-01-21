# 前端组件文档 (Component Documentation)

**负责人**: FrontendAgent  
**最后更新**: 2026-01-11  
**描述**: 本文档记录项目中核心组件的 API、使用方法及设计细节。
待更新。
---

## 1. 布局组件 (Layout)

### 1.1 Navbar
**路径**: `src/components/layout/Navbar.tsx`

**描述**: 
应用的顶部导航栏。采用现代化 Glassmorphism（毛玻璃）设计风格。包含 Logo、居中的导航菜单以及右侧的登录/用户信息区域。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `className` | `string` | `undefined` | 可选的额外 CSS 类名，用于合并样式 |

**依赖**:
- `lucide-react`: 用于图标 (BookOpen, Search, Upload, etc.)
- `AuthModalContext`: 用于触发全局登录弹窗

**代码示例**:
```tsx
import { Navbar } from '@/components/layout/Navbar';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen">
      <Navbar className="fixed top-0" />
      <main>{children}</main>
    </div>
  );
}
```

### 1.2 Sidebar
**路径**: `src/components/layout/Sidebar.tsx`

**描述**:
应用的侧边导航栏。支持折叠/展开，管理收藏夹列表。

**功能**:
- **折叠/展开**: 点击分隔线上的箭头按钮切换状态。
- **全局搜索**: 点击顶部的 "搜索论文" 按钮，重置当前视图为全局搜索模式（取消选中任何收藏夹）。
- **收藏夹管理**:
    - **新建**: 点击 "+" 号，出现带文件夹图标的输入框，输入名称回车即可创建。
    - **切换**: 点击列表项高亮选中，并触发 `onSelectCollection` 回调。
    - **重命名**: 悬浮列表项显示菜单，点击 "重命名" 进入编辑模式，失焦或回车保存。
    - **删除**: 悬浮列表项显示菜单，点击删除确认移除。
- **设置入口**: 底部固定设置按钮，触发用户级全局配置。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `className` | `string` | `undefined` | 样式类名 |
| `onSettingsClick` | `() => void` | `undefined` | 点击设置按钮的回调 |
| `onSelectCollection` | `(col: Collection | null) => void` | `undefined` | 选中收藏夹的回调，传入 null 表示重置/全局搜索 |

---

## 2. 认证模块 (Authentication)

认证模块采用 **全局弹窗 (Modal)** 模式，由 Context 控制状态，组件负责展示。

### 2.1 AuthModalContext
**路径**: `src/components/auth/AuthModalContext.tsx`

**描述**: 
管理全局认证弹窗的状态（开启/关闭）以及当前视图（登录/注册/找回密码）。

**API (useAuthModal)**:
| 方法/属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `isOpen` | `boolean` | 弹窗是否打开 |
| `view` | `'login' | 'register' | 'forgot-password'` | 当前展示的表单视图 |
| `openAuthModal` | `(view?: AuthView) => void` | 打开弹窗，可指定初始视图（默认 login） |
| `closeAuthModal` | `() => void` | 关闭弹窗 |
| `setAuthView` | `(view: AuthView) => void` | 切换当前视图 |

**使用示例**:
```tsx
'use client';
import { useAuthModal } from '@/components/auth/AuthModalContext';

export function LoginButton() {
  const { openAuthModal } = useAuthModal();
  return <button onClick={() => openAuthModal('login')}>登录</button>;
}
```

### 2.2 AuthModal
**路径**: `src/components/auth/AuthModal.tsx`

**描述**: 
认证弹窗的容器组件。监听 Context 状态，使用 `Dialog` 组件包裹具体的表单（Login/Register/Forgot）。

**特点**:
- 背景透明，去除了默认的 Dialog 样式，以适应内部组件的圆角设计。
- 自动处理关闭事件。

### 2.3 认证表单组件 (Forms)

包括 `LoginForm`, `RegisterForm`, `ForgotPasswordForm`。

**路径**: `src/components/auth/*.tsx`

**通用 Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `className` | `string` | `undefined` | 样式类名 |
| `isModal` | `boolean` | `false` | 是否在弹窗模式下运行。如果为 true，链接点击会切换 Context 视图而不是跳转页面。 |

**设计细节**:
- **左侧**: 品牌形象区，包含背景图、渐变遮罩和 Slogan。
- **右侧**: 交互表单区，包含输入框、操作按钮和切换链接。
- **响应式**: 在移动端 (md 以下) 自动隐藏左侧图片区，只展示表单。

**组件列表**:
- **LoginForm**: 邮箱/密码登录。

---

## 3. 搜索与检索模块 (Search & Retrieval)

### 3.1 SearchBar
**路径**: `src/components/search/SearchBar.tsx`

**描述**:
主搜索框组件。支持 AI 搜索模式切换和高级搜索配置。

**功能**:
- **搜索输入**: 实时响应用户输入。
- **AI 模式**: 左侧 Toggle 开关切换普通/AI 深度搜索。
- **配置气泡**: 右侧设置按钮点击弹出 `SearchSettings` Popover。

### 3.2 SearchSettings
**路径**: `src/components/search/SearchSettings.tsx`

**描述**:
搜索相关的局部配置面板。作为 Popover 依附于 SearchBar。

**配置项**:
- **AI 搜索配置**: 深度推理模式开关。
- **结果排序**: 相关性、时间、引用量排序。
- **过滤选项**: 年份范围、来源筛选。

### 3.3 SearchFilters
**路径**: `src/components/search/SearchFilters.tsx`

**描述**:
搜索结果页面的快捷筛选标签栏和操作区。

**功能**:
- **标签筛选**: 全部、标题、作者、摘要等快速过滤。
- **操作入口**: 
    - **AI 助手**: 触发 `onChatClick` 打开问答面板。
    - **上传论文**: 触发 `onUploadClick` 打开上传弹窗。

### 3.4 UploadModal
**路径**: `src/components/upload/UploadModal.tsx`

**描述**:
文件上传弹窗。支持 PDF 文件的拖拽上传和列表管理。

**功能**:
- **拖拽区域**: 视觉反馈明确的拖拽上传区。
- **文件验证**: 自动过滤非 PDF 文件。
- **列表管理**: 展示待上传文件，支持移除。
- **上传模拟**: 模拟上传进度条和成功/失败状态。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `isOpen` | `boolean` | `false` | 是否显示 |
| `onClose` | `() => void` | `undefined` | 关闭回调 |

### 3.5 SearchResults
**路径**: `src/components/search/SearchResults.tsx`

**描述**:
搜索结果列表展示组件。采用网格/表格布局展示论文核心信息。支持 AI 增强显示和收藏操作。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `results` | `Paper[]` | `[]` | 论文数据列表 |
| `className` | `string` | `undefined` | 样式类名 |
| `onToggleBookmark` | `(id: string) => void` | `undefined` | 点击收藏/取消收藏的回调 |
| `aiEnabled` | `boolean` | `false` | 是否开启 AI 增强显示 (评分与推荐理由) |

**展示字段**:
- **基础信息**: 标题、作者、年份、来源、引用数、摘要。
- **状态**: 收藏 (Bookmark) 按钮及状态高亮。
- **AI 增强 (当 aiEnabled=true)**:
    - **评分 (Score)**: 标题旁的动态颜色标签 (如 "AI 98")。
    - **推荐理由 (Reason)**: 摘要下方的 AI 生成推荐理由卡片。



## 4. 设置模块 (Settings)

### 4.1 SettingsModal
**路径**: `src/components/settings/SettingsModal.tsx`

**描述**:
用户级全局设置弹窗。

**功能**:
- **Tab 导航**: 通用、账号、通知、关于。
- **界面设置**: 深色模式、紧凑模式开关。
- **账号安全**: 修改密码、两步验证入口。

---

## 5. 阅读器模块 (Reader)

论文深度阅读页面的核心组件群，采用三栏布局（目录-正文-助手）。

### 5.1 ReaderPage (Page Wrapper)
**路径**: `src/app/reader/[id]/page.tsx`

**描述**:
阅读页面的顶层容器。负责协调各子组件的状态（如当前页码、侧边栏折叠、搜索关键词等），实现组件间的通信。

**功能**:
- **状态提升**: 管理 `currentPage`, `searchQuery` 等共享状态。
- **布局管理**: 采用 Flex 布局，固定视口高度 (`h-screen`)，确保 PDF 阅读区域独立滚动。

### 5.2 ReaderNavbar
**路径**: `src/components/reader/ReaderNavbar.tsx`

**描述**:
阅读页专属顶部导航栏。提供返回、标题展示、搜索入口及视图管理。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `title` | `string` | `"Untitled Paper"` | 论文标题 |
| `isBookmarked` | `boolean` | `false` | 是否已收藏 |
| `onSearch` | `(query: string) => void` | `undefined` | 搜索输入回调，用于触发 PDF 内容高亮 |
| `onToggleBookmark` | `() => void` | `undefined` | 收藏切换回调 |

**功能**:
- **搜索**: 实时输入触发 `onSearch`，联动 PDFViewer 进行高亮。
- **收藏**: 快速收藏/取消收藏当前论文。

### 5.3 ReaderSidebar
**路径**: `src/components/reader/ReaderSidebar.tsx`

**描述**:
左侧导航栏。提供论文大纲（目录）和缩略图视图切换。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `isCollapsed` | `boolean` | `false` | 是否折叠 |
| `onNavigate` | `(page: number) => void` | `undefined` | 点击目录项跳转页码的回调 |

**功能**:
- **多视图**: 支持 "目录 (Outline)" 和 "视图 (Layers)" 切换。
- **导航**: 点击目录项触发 `onNavigate`，联动 PDFViewer 跳转。

### 5.4 PDFViewer
**路径**: `src/components/reader/PDFViewer.tsx`

**描述**:
基于 `react-pdf` 封装的核心阅读组件。支持分页/滚动模式切换及关键词高亮。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `url` | `string` | - | PDF 文件地址 |
| `initialPage` | `number` | `1` | 初始页码 |
| `onPageChange` | `(page: number) => void` | `undefined` | 页码变更回调 |
| `searchQuery` | `string` | `''` | 搜索关键词，用于高亮匹配 |

**功能**:
- **双模式**: 支持 "翻页 (Pagination)" 和 "滚动 (Scroll)" 两种阅读模式。
- **搜索高亮**: 根据 `searchQuery` 自动高亮匹配文本（黄色背景）。
- **自适应**: 监听容器宽度变化，自动调整 PDF 渲染比例。

### 5.5 ReaderRightPanel
**路径**: `src/components/reader/ReaderRightPanel.tsx`

**描述**:
右侧 AI 助手与工具面板。集成导读、笔记、脑图等多个功能 Tab。

**功能**:
- **Tab 切换**: 顶部导航条切换不同功能区。
- **内容区**: 动态渲染对应的 Tab 组件 (`GuideTab`, `NotesTab` 等)。

### 5.6 功能 Tabs
**路径**: `src/components/reader/tabs/*.tsx`

**组件列表**:
- **GuideTab**: AI 导读与对话。包含预设问题（Quick Prompts）和对话记录流。
- **NotesTab**: 笔记管理。支持添加新笔记和查看历史笔记列表。
- **GraphTab**: 知识图谱视图容器。
  - 作为一个 `Client Component` 包装器。
  - 负责动态导入 (`next/dynamic`) `GraphViz` 组件并设置 `ssr: false`，确保 WebGL 相关代码仅在客户端执行。
  - 显示加载状态 (Loading Spinner)。
- **ReportTab**: 深度研究报告模块。
  - 采用列表/详情 (Master-Detail) 双层结构。
  - **列表页**: 展示已生成的报告任务及其状态（完成、生成中、失败）。
  - **详情页**: 
    - 渲染 Markdown 格式的深度分析报告。
    - 支持 SSE (Server-Sent Events) 流式生成状态展示。
    - 提供复制和 PDF 导出功能。
- **SettingsTab**: 阅读器偏好设置（主题、字号等）。

### 5.7 GraphViz (知识图谱核心)
**路径**: `src/components/reader/tabs/GraphViz.tsx`

**描述**:
基于 `reagraph` (WebGL) 的交互式知识图谱渲染组件。展示论文核心概念及其关联。

**核心功能**:
- **可视化渲染**: 使用力导向布局 (Force Directed Layout) 展示节点与连线。
- **交互控制**:
  - **缩放/平移**: 支持鼠标滚轮缩放和拖拽平移。
  - **节点交互**: 悬浮显示详情，拖拽节点调整位置。
  - **工具栏**:
    - **适应视图 (Focus)**: 自动调整视角以包含所有节点。
    - **重置视角 (Reset)**: 恢复默认中心视角。
- **样式定制**:
  - 配置 `lasso`、`node`、`edge` 的颜色与样式。
  - 采用 Glassmorphism 风格的悬浮控件。

**技术要点 (Web Worker 兼容性)**:
由于 `reagraph` 依赖的 `troika-worker-utils` 在 Next.js App Router 环境下存在兼容性问题（Worker 中 `window` 未定义），采取了以下特殊处理：
1. **源码补丁**: 直接修补了 `node_modules/troika-worker-utils/dist/troika-worker-utils.esm.js`。
   - 在 Worker Bootstrap 代码中注入 `self.window = self;` Polyfill。
2. **构建配置**: 在 `next.config.mjs` 中添加 `transpilePackages: ['reagraph', 'troika-worker-utils', ...]`。
3. **动态加载**: 必须通过 `GraphTab` 进行 `ssr: false` 的动态加载，严禁直接在服务端组件中引入。

### 5.8 PDFPageOverlay
**路径**: `src/components/reader/PDFPageOverlay.tsx`

**描述**:
PDF 单页的覆盖层组件，负责处理标注渲染、用户交互操作及辅助工具（翻译）的展示。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `pageIndex` | `number` | - | 当前页索引 (0-based) |
| `scale` | `number` | - | 当前缩放比例 (主要用百分比定位，scale 用于辅助计算) |
| `layers` | `Layer[]` | `[]` | 图层列表 |
| `activeLayerId` | `string` | - | 激活图层 ID |
| `onAddAnnotation` | `(ann: Annotation) => void` | `undefined` | 新增标注回调 |
| `onUpdateAnnotation` | `(ann: Annotation) => void` | `undefined` | 更新标注内容/样式回调 |
| `onDeleteAnnotation` | `(id: string) => void` | `undefined` | 删除标注回调 |

**核心功能与交互设计**:

1. **无阻碍标注 (Pass-Through Interaction)**:
   - **机制**: 所有渲染在页面上的标注元素（高亮、下划线）均设置 `pointer-events-none`。
   - **目的**: 解决传统覆盖层遮挡底层文字的问题。用户可以透过已有的高亮层，继续对底层文字进行拖拽选择（实现多重高亮叠加）或点击操作。
   - **事件代理**: 为了保留对标注的点击编辑能力，组件在父级容器层实现了点击 (`onClick`) 和悬停 (`onMouseMove`) 的手动坐标检测算法，智能判断用户意图。

2. **多功能标注系统**:
   - **高亮 (Highlight)**: 
     - 提供 5 种预设颜色（黄/绿/蓝/红/紫）。
     - 支持点击后修改颜色或删除。
   - **笔记 (Note)**: 
     - **样式**: 红色虚线下划线（加粗 3px），视觉醒目且不遮挡文字。
     - **悬停预览**: 鼠标滑过笔记区域时，自动弹出白色卡片式预览框（Card Style），展示完整内容。
     - **编辑体验**: 点击即弹出编辑框，支持 `Enter` 快捷保存。
   - **翻译 (Translation - Transient Mode)**:
     - **临时弹窗**: 选中文字点击翻译后，不立即生成持久化标注，而是显示一个层级极高 (`z-50`) 的临时悬浮卡片。
     - **一键转存**: 只有当用户点击“保存为备注”时，才将翻译结果（原文+译文）转化为持久化的笔记标注。
     - **优势**: 避免页面被大量临时性的翻译下划线污染，保持阅读区整洁。

3. **UI/UX 细节**:
   - **白色工具栏**: 选中文本后自动弹出的 Toolbar 采用白色圆角卡片设计，带深色阴影，符合系统整体风格。
   - **自动聚焦**: 创建备注时自动打开输入框并聚焦，减少点击次数。
   - **智能定位**: 弹窗位置根据选区自动计算，确保不遮挡选中文本。

