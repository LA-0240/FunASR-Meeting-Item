# ASR 会议智能助手 - 前端

基于 Vue 3 + Vite 构建的智能会议转写与分析系统前端，提供音频/视频上传、语音识别、会议纪要生成、声纹管理、智能问答等功能。

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | ^3.5.32 | 渐进式 JavaScript 框架，使用 Composition API |
| Vue Router | ^4.6.4 | Vue.js 官方路由管理器 |
| Axios | ^1.15.1 | HTTP 客户端，用于后端 API 通信 |
| Marked | ^18.0.2 | Markdown 解析器，用于渲染富文本内容 |
| Vite | ^8.0.9 | 下一代前端构建工具 |
| @vitejs/plugin-vue | ^6.0.6 | Vite 的 Vue 3 单文件组件支持插件 |

## 项目结构

```
src/
├── api/                      # API 接口层
│   ├── index.js              # Axios 实例配置与拦截器
│   ├── asrApi.js             # 语音识别相关 API
│   ├── meetingApi.js         # 会议内容管理 API
│   ├── fileApi.js            # 文件管理 API
│   ├── userApi.js            # 用户管理 API
│   ├── speakerApi.js         # 说话人管理 API
│   ├── voiceprintApi.js      # 声纹管理 API
│   ├── ragApi.js             # 智能问答 (RAG) API
│   ├── promptApi.js          # 提示词模板 API
│   └── exportApi.js          # 文档导出 API
├── assets/                   # 静态资源
├── components/               # 通用组件
├── router/
│   └── index.js              # 路由配置与导航守卫
├── views/                    # 页面视图
│   ├── LoginView.vue         # 登录/注册页
│   ├── HomeView.vue          # 主布局（侧边栏 + 内容区）
│   ├── ConferenceView.vue    # 会议文件列表页
│   ├── MeetingDetailView.vue # 会议详情页
│   ├── VoiceprintView.vue    # 声纹管理页
│   ├── TemplateView.vue      # 模板管理页
│   ├── UserView.vue          # 用户中心页
│   └── meeting-detail/       # 会议详情子组件
│       ├── DetailHeader.vue      # 详情页头部
│       ├── MediaPlayer.vue       # 媒体播放器
│       ├── MeetingStats.vue      # 会议统计
│       ├── MeetingChatPanel.vue  # 智能问答聊天面板
│       └── modals/               # 模态框组件
│           ├── ConfirmModal.vue      # 确认对话框
│           ├── LoadingModal.vue      # 加载提示框
│           └── ResultModal.vue       # 结果提示框
├── App.vue                   # 根组件
├── main.js                   # 应用入口
└── style.css                 # 全局样式
```

## 功能模块

### 1. 用户认证模块

- **登录/注册**：支持用户名密码登录，带有翻转卡片动画效果的登录/注册切换界面
- **Token 认证**：基于 Bearer Token 的身份认证，Token 存储于 localStorage
- **路由守卫**：未登录用户自动跳转至登录页
- **用户信息持久化**：用户信息、权限状态本地存储

### 2. 会议文件管理

- **文件上传**：支持音频/视频文件上传，支持上传后自动转录
- **文件列表**：网格视图/列表视图切换，按文件类型（全部/音频/视频）筛选
- **文件搜索**：按文件名关键词搜索
- **文件操作**：重命名、删除、修改会议类型标签
- **上传进度**：实时显示文件上传进度

### 3. 会议详情

会议详情页提供以下功能标签页：

#### 会议纪要
- AI 自动生成结构化会议纪要
- 支持手动编辑和重新生成
- Markdown 富文本渲染展示

#### 会议摘要
- 简短精炼的会议内容摘要
- 支持编辑和重新生成

#### 时间轴（会议分段）
- 按主题自动分段的会议内容时间轴
- 每段包含标题、摘要、起止时间
- 点击分段可跳转至对应音频/视频位置
- 支持分段信息编辑

#### 逐字稿
- 完整的语音转文字结果，带说话人标注
- 支持关键词搜索
- 支持逐句编辑修改文本和说话人
- 点击句子跳转播放对应音频

#### 智能问答
- 基于 RAG 技术的会议内容智能问答
- 文件自动向量化索引
- 支持多轮对话，聊天历史本地存储
- 回答附带来源引用（逐字稿、分段、工具调用等）
- 支持 Markdown 富文本回答渲染

### 4. 媒体播放器

- 自动识别音频/视频文件类型
- 原生 HTML5 媒体播放控制
- 支持跳转到指定时间点
- 播放/暂停编程控制
- 加载错误处理

### 5. 声纹管理

- **说话人管理**：创建、编辑、删除说话人档案
- **声纹管理**：为说话人添加/删除/更新声纹样本
- **声纹播放**：在线播放声纹音频
- **头像管理**：说话人头像上传与删除
- **搜索功能**：按名称搜索说话人/声纹

### 6. 模板管理

- **模板列表**：管理会议纪要和摘要的提示词模板
- **模板操作**：创建、编辑、复制、删除模板
- **模板分类**：按模板类型（纪要/摘要）分类管理

### 7. 用户中心

- **个人资料**：查看和编辑用户基本信息
- **头像管理**：上传/删除用户头像
- **用户统计**：显示会议数量、时长等统计数据
- **快捷入口**：一键跳转至核心功能页面

### 8. 文档导出

- 逐字稿导出为 Word 文档
- 会议纪要导出为 Word 文档
- 会议摘要导出为 Word 文档
- 自动触发浏览器下载

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 7.0.0

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

启动后访问 http://localhost:5173

### 生产构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览构建

```bash
npm run preview
```

本地预览生产构建结果。

## API 配置

后端 API 基础地址在 `src/api/index.js` 中配置：

```javascript
export const API_BASE_URL = 'http://localhost:8000';
```

如需修改后端地址，请修改此配置。

### 请求拦截器

- 自动从 localStorage 获取 Token 并添加到 `Authorization` 请求头
- Token 格式：`Bearer {token}`

### 响应拦截器

- 普通请求返回 `response.data`
- Blob 类型请求（文件下载）返回完整 `response` 对象
- 统一错误日志输出

## 组件架构

### 页面级组件

| 组件 | 路径 | 说明 |
|------|------|------|
| LoginView | views/LoginView.vue | 登录/注册页面 |
| HomeView | views/HomeView.vue | 主布局，包含侧边栏导航 |
| ConferenceView | views/ConferenceView.vue | 会议文件列表 |
| MeetingDetailView | views/MeetingDetailView.vue | 会议详情主页面 |
| VoiceprintView | views/VoiceprintView.vue | 声纹管理 |
| TemplateView | views/TemplateView.vue | 模板管理 |
| UserView | views/UserView.vue | 用户中心 |

### 功能子组件

| 组件 | 路径 | 说明 |
|------|------|------|
| DetailHeader | views/meeting-detail/DetailHeader.vue | 详情页头部（返回按钮、标题、时间） |
| MediaPlayer | views/meeting-detail/MediaPlayer.vue | 音视频播放器 |
| MeetingStats | views/meeting-detail/MeetingStats.vue | 会议统计卡片 |
| MeetingChatPanel | views/meeting-detail/MeetingChatPanel.vue | RAG 智能问答聊天面板 |

### 模态框组件

| 组件 | 路径 | 说明 |
|------|------|------|
| ConfirmModal | views/meeting-detail/modals/ConfirmModal.vue | 二次确认对话框 |
| LoadingModal | views/meeting-detail/modals/LoadingModal.vue | 加载状态提示 |
| ResultModal | views/meeting-detail/modals/ResultModal.vue | 操作结果提示（成功/失败） |

## 路由说明

| 路径 | 组件 | 说明 | 权限 |
|------|------|------|------|
| `/login` | LoginView | 登录/注册页 | 公开 |
| `/` | HomeView | 主布局（重定向到会议列表） | 需登录 |
| `/conference` | ConferenceView | 会议文件列表 | 需登录 |
| `/conference/:id` | MeetingDetailView | 会议详情 | 需登录 |
| `/voiceprint` | VoiceprintView | 声纹管理 | 需登录 |
| `/template` | TemplateView | 模板管理 | 需登录 |
| `/user` | UserView | 用户中心 | 需登录 |

## 特色功能

### RAG 智能问答

- **自动索引**：进入会议详情时自动触发文件向量化索引
- **异步索引**：索引过程异步执行，支持状态轮询
- **来源引用**：AI 回答附带参考来源，包括逐字稿片段、分段摘要、工具调用结果等
- **工具调用**：支持发言统计、完整逐字稿、发言人过滤、时间范围查询、关键词搜索、分段检索等工具
- **本地存储**：聊天历史按用户和文件独立存储于 localStorage

### 响应式设计

- 侧边栏导航自适应
- 文件列表支持网格/列表两种视图
- 聊天面板自适应高度
- 模态框居中显示

### 错误处理

- API 请求统一错误捕获与日志输出
- 媒体加载失败处理
- 表单验证与提示
- 操作结果反馈（成功/失败弹窗）
