# FunASR-Meeting-Item - 基于 FunASR 的 AI 智能会议纪要系统

> 毕业设计项目 —— 集语音识别、声纹识别、会议摘要生成、语义分段、RAG 智能问答于一体的全栈智能会议处理系统

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [项目结构](#项目结构)
- [功能模块](#功能模块)
- [快速开始](#快速开始)
- [数据模型](#数据模型)
- [API 接口概览](#api-接口概览)
- [技术亮点](#技术亮点)
- [许可证](#许可证)

---

## 项目简介

本项目是一个基于 **FunASR** + **大语言模型** + **RAG** 的智能会议纪要系统，提供从音频/视频上传、语音识别、说话人分离、会议纪要生成到智能问答的一站式会议智能化解决方案。

系统采用前后端分离架构：
- **后端**：Django + FunASR + ChromaDB，提供语音识别、声纹匹配、LLM 摘要、向量检索等核心能力
- **前端**：Vue 3 + Vite，提供直观易用的 Web 操作界面

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 🎙️ **高精度语音识别** | 基于 FunASR paraformer-zh 模型，支持 VAD、标点恢复、热词增强 |
| 👥 **说话人分离与声纹匹配** | 两步法识别：先分离说话人，再与声纹库匹配，支持一人多声纹 |
| 📝 **智能会议纪要** | LLM 生成结构化纪要（议题、参与人、讨论内容、决议、待办事项） |
| 📊 **多维度会议分析** | 说话人分析、时间分布、主题分析、决策分析等 5 大维度 |
| 🔍 **RAG 智能问答** | 基于向量检索的会议内容问答，支持工具调用和来源引用 |
| 📑 **语义分段** | 自动按主题切分会议内容，生成时间轴式浏览体验 |
| 🔊 **声纹管理** | 说话人档案管理、声纹样本增删改、在线播放 |
| 📄 **Word 导出** | 逐字稿、纪要、摘要一键导出 Word 文档 |
| 👤 **用户系统** | Token 认证、个人资料、头像管理、数据权限隔离 |
| 📱 **响应式前端** | Vue 3 构建，支持网格/列表视图、Markdown 渲染 |

---

## 技术架构

### 前端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | ^3.5.32 | 渐进式 JavaScript 框架，使用 Composition API |
| Vue Router | ^4.6.4 | Vue.js 官方路由管理器 |
| Axios | ^1.15.1 | HTTP 客户端，用于后端 API 通信 |
| Marked | ^18.0.2 | Markdown 解析器，用于渲染富文本内容 |
| Vite | ^8.0.9 | 下一代前端构建工具 |
| @vitejs/plugin-vue | ^6.0.6 | Vite 的 Vue 3 单文件组件支持插件 |

### 后端技术栈

| 类别 | 技术 |
|------|------|
| Web 框架 | Django 6.0 + Django REST Framework |
| 语音识别 | FunASR（paraformer-zh + fsmn-vad + ct-punc + cam++） |
| 声纹识别 | damo/speech_campplus_sv_zh-cn_16k-common |
| 大语言模型 | Qwen/Qwen3.5-35B-A3B（ModelScope API） |
| 向量数据库 | ChromaDB |
| Embedding 模型 | BAAI/bge-base-zh-v1.5 |
| 数据库 | SQLite3 |
| 认证方式 | Token Authentication |

---

## 项目结构

```
FunASR-Meeting-Item/
├── asr-backend/                          # 后端项目
│   ├── README.md                         # 后端文档
│   └── asr_meeting_service/              # Django 项目根目录
│       ├── asr_api/                      # 核心 API 应用
│       │   ├── views/                    # API 视图层（14 个功能模块）
│       │   ├── rag/                      # RAG 检索增强生成模块
│       │   ├── models.py                 # 数据模型定义
│       │   ├── urls.py                   # API 路由配置
│       │   └── migrations/               # 数据库迁移文件
│       ├── asr_meeting_service/          # Django 项目配置
│       ├── manage.py                     # Django 管理命令
│       ├── requirements_rag.txt          # RAG 模块依赖
│       ├── chroma_db/                    # ChromaDB 向量数据库存储
│       ├── uploaded_files/               # 上传文件存储目录
│       └── media/                        # 媒体文件（头像、声纹音频等）
│
├── asr-frontend/                         # 前端项目
│   └── asr-frontend/                     # Vue 项目根目录
│       ├── README.md                     # 前端文档
│       ├── src/
│       │   ├── api/                      # API 接口层（9 个模块）
│       │   ├── views/                    # 页面视图（7 个页面 + 子组件）
│       │   ├── router/                   # 路由配置
│       │   ├── components/               # 通用组件
│       │   └── assets/                   # 静态资源
│       ├── package.json
│       └── vite.config.js
│
├── 其余文档/                             # 其他测试文档
└── README.md                             # 项目说明（本文件）
```

---

## 功能模块

### 1. 用户认证系统

| 功能 | 说明 |
|------|------|
| 用户注册 | 支持用户名、邮箱、密码注册 |
| 用户登录 | Token 认证，返回 API 令牌 |
| 用户登出 | 注销当前 Token |
| 个人资料 | 查看/更新用户基本信息 |
| 头像管理 | 上传/删除用户头像 |
| 路由守卫 | 前端未登录自动跳转登录页 |

**认证机制**：基于 Django REST Framework 的 TokenAuthentication，支持 Bearer Token 格式。

---

### 2. ASR 语音识别

基于 FunASR 框架，支持多说话人声纹识别，采用**两步法**：分离→切割→匹配。

**功能特性：**
- **语音转文字**：基于 paraformer-zh 模型的中文语音识别
- **说话人分离**：cam++ 模型进行说话人日志（Speaker Diarization）
- **标点恢复**：ct-punc 模型自动添加标点符号
- **VAD 语音活动检测**：fsmn-vad 模型检测有效语音段
- **声纹匹配两步法**：
  1. FunASR 进行说话人分离 + ASR 识别
  2. 对每个说话人切割音频片段，提取声纹特征，与用户声纹库匹配
- **多片段特征融合**：取每个说话人 TOP 3 最长片段的特征平均值
- **热词支持**：支持自定义热词提高特定词汇识别率

**支持的格式**：
- 音频：`.wav`, `.mp3`, `.ogg`, `.flac`
- 视频：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`（自动提取音频）

---

### 3. 会议纪要与摘要

| 功能 | 说明 |
|------|------|
| 会议纪要生成 | 生成结构化会议纪要（议题、参与人、讨论内容、决议、待办事项） |
| 会议摘要生成 | 生成轻量化摘要（支持 short/medium/long 三种长度） |
| 纪要/摘要编辑 | 用户手动编辑内容 |
| 模板系统 | 支持默认模板和自定义模板，分为"纪要"和"摘要"两种类型 |

**Prompt 模板优先级**：自定义 Prompt > 模板 Prompt > 默认 Prompt

---

### 4. 会议语义分段

**功能特点：**
1. **初分段**：基于说话人切换和内容长度进行初步分段
2. **LLM 优化**：使用大语言模型为每个分段生成标题和核心总结
3. **批量处理**：支持批量 LLM 调用优化，失败时回退到逐个处理
4. **容错机制**：LLM 调用或解析失败时自动使用默认值

---

### 5. 会议多维度分析

**五大分析维度：**

| 分析类型 | 说明 |
|----------|------|
| **说话人分析** | 发言人列表、发言次数/时长、发言占比、角色判定（主导者/积极参与者/参与者/沉默参与者） |
| **会议概览** | 总时长、发言人数、平均发言时长、发言密度、会议效率评估 |
| **时间分布** | 发言热度时间轴、高峰时段识别、峰值时间定位 |
| **主题分析** | 会议主题提取、各主题讨论时长占比 |
| **决策分析** | 会议决策提取、行动项识别、跟进建议 |

---

### 6. 声纹识别系统

**功能特性：**
- **声纹提取**：使用 campplus 模型提取 192 维声纹特征向量
- **声纹匹配**：余弦相似度计算，动态阈值调整（说话人多时降低阈值）
- **一人多声纹**：每个说话人支持多条声纹记录，取最高相似度匹配
- **自动声纹追加**：会议中自动采集匹配到的说话人声纹（来源标注为"自动采集"）
- **声纹去重**：自动声纹相似度 ≥ 96% 时不重复添加
- **声纹数量控制**：每个说话人最多保留 4 条声纹

---

### 7. 说话人管理系统

**功能特性：**
- 说话人 CRUD（增删改查）
- 说话人头像管理
- 说话人关联多条声纹
- 声纹来源区分：手动注册 / 会议自动采集

**数据模型关系：**
```
User (1) ──→ (N) Speaker (1) ──→ (N) Voiceprint
```

---

### 8. RAG 智能问答系统

#### 模块架构

```
用户提问
   ↓
MeetingAgent (智能会议助手)
   ├─ LLM 工具决策 → 判断是否需要调用工具
   ├─ 6 种专业工具:
   │   ├─ SPEAKER_STATS    发言统计工具
   │   ├─ FULL_TRANSCRIPT  完整逐字稿工具
   │   ├─ SPEAKER_FILTER   发言人过滤工具
   │   ├─ TIME_RANGE_QUERY 时间范围查询工具
   │   ├─ KEYWORD_SEARCH   关键词搜索工具
   │   └─ SEGMENT_RETRIEVER 分段检索工具
   ├─ Retriever (向量检索)
   │   ├─ VectorStore (ChromaDB)
   │   └─ EmbeddingService (BGE 模型)
   └─ LLM 生成回答 → 返回(answer, sources, thinking)
```

#### 索引数据类型
- 逐字稿（transcript）- 语义分块
- 会议纪要（summary）
- 会议摘要（abstract）
- 会议分段内容（segment）
- 分段摘要（segment_summary）

#### 前端交互
- 文件自动向量化索引（进入详情页时自动触发）
- 异步索引 + 状态轮询
- 聊天历史本地存储（按用户和文件隔离）
- 回答附带来源引用展示
- Markdown 富文本渲染

---

### 9. 文件管理系统

**功能特性：**
- 文件上传（音频/视频）
- 上传后自动转录
- 文件列表查询（网格/列表视图）
- 文件搜索与筛选（按类型、名称）
- 文件重命名、删除
- 文件下载
- 文件状态追踪（original/processed）

---

### 10. Word 文档导出

**支持导出类型：**
- 逐字稿导出（含说话人、时间戳）
- 会议纪要导出
- 会议摘要导出

使用 python-docx 库生成 .docx 文件，包含标题、生成时间、格式化正文。

---

### 11. 模板管理

- 管理会议纪要和摘要的提示词模板
- 支持模板创建、编辑、复制、删除
- 按模板类型（纪要/摘要）分类管理

---

### 12. 用户中心

- 个人资料查看与编辑
- 头像上传/删除
- 用户统计数据展示
- 快捷功能入口

---

## 快速开始

### 环境要求

| 环境 | 要求 |
|------|------|
| Python | 3.10+ |
| Node.js | 16.0+ |
| npm | 7.0+ |
| ffmpeg | 已安装（音频/视频处理依赖） |
| 内存 | 建议 8GB+（加载 AI 模型需要） |

### 后端启动

```bash
# 1. 进入后端项目目录
cd asr-backend/asr_meeting_service

# 2. 安装基础依赖
pip install django djangorestframework django-cors-headers python-docx ffmpeg-python funasr modelscope openai

# 3. 安装 RAG 模块依赖
pip install -r requirements_rag.txt

# 国内源加速（可选）
# pip install -r requirements_rag.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 5. 初始化 Prompt 模板
python manage.py init_prompt_templates

# 6. 创建超级用户（可选）
python manage.py createsuperuser

# 7. 启动服务
python manage.py runserver 0.0.0.0:8000
```

**后端访问地址：**
- API 服务：http://localhost:8000/
- Django 管理后台：http://localhost:8000/admin/
- 健康检查：http://localhost:8000/

### 前端启动

```bash
# 1. 进入前端项目目录
cd asr-frontend/asr-frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

**前端访问地址：** http://localhost:5173

### 生产构建

```bash
# 前端构建
cd asr-frontend/asr-frontend
npm run build
# 构建产物输出到 dist/ 目录
```

### 配置说明

#### 后端配置

主要配置在 `asr-backend/asr_meeting_service/asr_meeting_service/settings.py` 中。

##### 大语言模型（LLM）API 配置

项目使用 ModelScope 的大语言模型 API 进行会议纪要生成、摘要、智能问答等功能。配置位于 `settings.py` 的 `LLM_CONFIG` 字典中：

```python
LLM_CONFIG = {
    "api_key": "ms-d1b982a8-f8f5-4025-b207-21119f33c11d",  # 替换为实际Token
    "base_url": "https://api-inference.modelscope.cn/v1/",
    "model_name": "Qwen/Qwen3.5-35B-A3B"    
}
```

**配置项说明：**

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `api_key` | ModelScope API 密钥（Token） | `ms-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `base_url` | API 服务地址 | `https://api-inference.modelscope.cn/v1/` |
| `model_name` | 使用的模型名称 | `Qwen/Qwen3.5-35B-A3B` |

**如何更换模型 API：**

1. **获取 API Key**
   - 访问 [ModelScope 官网](https://modelscope.cn/)
   - 注册/登录账号
   - 进入「个人中心」→「API 密钥」创建新的 Token
   - 复制生成的 API Key

2. **修改配置文件**
   - 打开 `asr-backend/asr_meeting_service/asr_meeting_service/settings.py`
   - 找到 `LLM_CONFIG` 配置段（约第 170 行）
   - 将 `api_key` 的值替换为你的 Token
   - 如需更换模型，修改 `model_name` 为目标模型名称
   - 如需使用其他 API 服务（如 OpenAI 兼容接口），修改 `base_url` 为对应地址

3. **更换为其他模型示例**

   ```python
   # 示例 1：使用 ModelScope 上的其他模型
   LLM_CONFIG = {
       "api_key": "你的API密钥",
       "base_url": "https://api-inference.modelscope.cn/v1/",
       "model_name": "qwen/Qwen2.5-72B-Instruct"
   }
   
   # 示例 2：使用 OpenAI 兼容接口
   LLM_CONFIG = {
       "api_key": "sk-xxxxxxxxxx",
       "base_url": "https://api.openai.com/v1/",
       "model_name": "gpt-4o"
   }
   
   # 示例 3：使用本地部署的模型（如 Ollama）
   LLM_CONFIG = {
       "api_key": "不需要密钥可留空",
       "base_url": "http://localhost:11434/v1/",
       "model_name": "qwen2.5:7b"
   }
   ```

> **安全提示**：生产环境建议使用环境变量存储 API Key，避免硬编码到代码中。可以修改 `settings.py` 为：
> ```python
> import os
> LLM_CONFIG = {
>     "api_key": os.environ.get("LLM_API_KEY", "默认key"),
>     "base_url": os.environ.get("LLM_BASE_URL", "https://api-inference.modelscope.cn/v1/"),
>     "model_name": os.environ.get("LLM_MODEL", "Qwen/Qwen3.5-35B-A3B")
> }
> ```

##### RAG 与 Embedding 模型配置

RAG（检索增强生成）模块的配置位于 `asr-backend/asr_meeting_service/asr_api/rag/config.py` 的 `RAGConfig` 类中。

**Embedding 模型配置：**

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-base-zh-v1.5` | Embedding 模型名称（BGE 中文轻量版） |
| `EMBEDDING_DEVICE` | `cpu` | 运行设备（有 GPU 可改为 `"cuda"`） |

**如何更换 Embedding 模型：**

打开 `asr-backend/asr_meeting_service/asr_api/rag/config.py`，找到 `RAGConfig` 类中的对应配置：

```python
# 轻量版（默认）
EMBEDDING_MODEL_NAME = "BAAI/bge-base-zh-v1.5"

# 完整版（注释中备用，效果更好但更慢）
# EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
```

如需使用 GPU 加速，修改：
```python
EMBEDDING_DEVICE = "cuda"  # 改为 "cuda"，默认是 "cpu"
```

> **注意**：Embedding 模型为本地离线运行（BGE 模型），首次运行会自动下载并缓存到 `hf_cache/` 目录，后续运行无需联网。已强制开启离线模式确保数据隐私。

**其他 RAG 配置项：**

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `CHROMA_PERSIST_DIR` | `chroma_db/` | ChromaDB 向量数据库存储目录 |
| `CHUNK_SIZE` | `512` | 文本分块大小（字符数） |
| `CHUNK_OVERLAP` | `50` | 文本块重叠大小 |
| `VECTOR_SEARCH_TOP_K` | `10` | 向量检索初筛返回数量 |
| `USE_RERANKER` | `False` | 是否启用 Reranker 重排序 |
| `MAX_HISTORY_LENGTH` | `10` | 对话历史保留轮数 |

##### 其他配置项

- `ALLOWED_EXTENSIONS`：支持的音频格式
- `ALLOWED_VIDEO_EXTENSIONS`：支持的视频格式
- `FILE_UPLOAD_DIR`：文件上传目录
- `TEMP_DIR`：临时文件目录
- `VOICEPRINT_DIR`：声纹文件目录

#### 前端配置

后端 API 基础地址在 `asr-frontend/asr-frontend/src/api/index.js` 中配置：

```javascript
export const API_BASE_URL = 'http://localhost:8000';
```

---

## 数据模型

| 模型 | 说明 | 主要字段 |
|------|------|----------|
| **User** | 用户模型（扩展 Django User） | email, avatar, created_at, updated_at |
| **UploadedFile** | 上传文件 | user, original_name, stored_name, file_path, file_type, file_size, status, meeting_type |
| **Transcription** | 转录记录 | file(一对一), transcription_text, segments(JSON) |
| **MeetingSummary** | 会议纪要 | file(一对一), summary_text, abstract_text, is_customized |
| **MeetingSegment** | 会议分段 | file, user, segment_index, start_time, end_time, title, content, summary, is_edited |
| **Speaker** | 说话人 | user, name, avatar |
| **Voiceprint** | 声纹信息 | speaker, user, feature(二进制), audio_file, source_type, source_meeting |
| **Prompt** | Prompt 模板 | user, name, system_prompt, user_prompt, category, template_type |

---

## API 接口概览

共 **30+** 个 API 接口，分为以下类别：

| 类别 | 接口数量 | 说明 |
|------|----------|------|
| 基础接口 | 1 | 健康检查 |
| ASR 接口 | 2 | 音频 ASR、视频 ASR |
| 会议纪要/摘要 | 8 | 生成、获取、编辑、分段 |
| 会议分析 | 1 | 多维度分析 |
| Word 导出 | 3 | 逐字稿、纪要、摘要 |
| 声纹管理 | 7 | 增删改查、音频、头像 |
| 说话人管理 | 9 | 增删改查、声纹管理 |
| 用户管理 | 6 | 注册、登录、资料、头像 |
| 文件管理 | 5 | 上传、列表、重命名、删除、下载 |
| 逐字稿管理 | 4 | 获取、搜索、编辑、生成 |
| Prompt 模板 | 5 | 增删改查、列表 |
| RAG 智能问答 | 4 | 聊天、索引、状态、测试 |

完整接口定义见后端 `asr_api/urls.py`。

---

## 技术亮点

### 后端
1. **两步法声纹识别**：先 FunASR 分离说话人，再切割音频提取声纹匹配，准确率更高
2. **多片段特征平均**：取 TOP 3 最长片段特征平均，减少单片段噪声影响
3. **动态阈值调整**：根据说话人数量动态调整声纹匹配阈值
4. **LLM 工具调用 Agent**：智能判断问题类型，选择最优工具处理
5. **语义分块索引**：按句子边界智能切分文本，保持语义完整性
6. **离线 Embedding**：BGE 模型本地运行，保护数据隐私
7. **容错降级机制**：LLM 调用失败时有完整的回退方案
8. **一人多声纹**：支持多条声纹，自动追加和去重
9. **单例懒加载**：AI 模型采用单例模式和懒加载，节省内存资源
10. **完整的数据权限隔离**：所有用户数据严格按用户 ID 隔离

### 前端
1. **组件化架构**：清晰的页面级组件 + 功能子组件 + 模态框组件分层
2. **9 个 API 模块**：按业务领域清晰划分的接口层
3. **RAG 聊天体验**：打字动画、来源引用、Markdown 渲染、本地历史
4. **双视图切换**：文件列表支持网格/列表两种视图模式
5. **响应式设计**：侧边栏自适应、聊天面板自适应高度
6. **统一错误处理**：API 请求统一错误捕获与日志输出

---

## 前端路由说明

| 路径 | 页面 | 权限 |
|------|------|------|
| `/login` | 登录/注册页 | 公开 |
| `/` | 主布局（重定向到会议列表） | 需登录 |
| `/conference` | 会议文件列表 | 需登录 |
| `/conference/:id` | 会议详情 | 需登录 |
| `/voiceprint` | 声纹管理 | 需登录 |
| `/template` | 模板管理 | 需登录 |
| `/user` | 用户中心 | 需登录 |

---

## 许可证

本项目仅供学习和研究使用。
