# ASR-Backend - 智能会议纪要生成系统后端

基于 **Django + FunASR + LLM** 的智能会议纪要生成系统后端服务。集语音识别、声纹识别、会议摘要生成、语义分段、RAG智能问答等功能于一体，为用户提供完整的会议音频/视频智能化处理解决方案。

## 目录

- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [核心功能](#核心功能)
- [数据模型](#数据模型)
- [API接口](#api接口)
- [快速启动](#快速启动)
- [技术亮点](#技术亮点)

---

## 技术栈

| 类别 | 技术 |
|------|------|
| Web框架 | Django 6.0 + Django REST Framework |
| 语音识别 | FunASR（paraformer-zh + fsmn-vad + ct-punc + cam++） |
| 声纹识别 | damo/speech_campplus_sv_zh-cn_16k-common |
| 大语言模型 | Qwen/Qwen3.5-35B-A3B（ModelScope API） |
| 向量数据库 | ChromaDB |
| Embedding模型 | BAAI/bge-base-zh-v1.5 |
| 数据库 | SQLite3 |
| 认证方式 | Token Authentication |

---

## 项目结构

```
asr-backend/asr_meeting_service/
├── asr_api/                          # 核心API应用
│   ├── views/                        # API视图层（14个功能模块）
│   │   ├── base.py                   # 健康检查接口
│   │   ├── asr.py                    # ASR语音识别接口
│   │   ├── video.py                  # 视频ASR接口
│   │   ├── meeting.py                # 会议纪要/摘要/分段接口
│   │   ├── meeting_analysis.py       # 会议多维度分析接口
│   │   ├── upload_transcribe.py      # 文件上传即转录接口
│   │   ├── transcription.py          # 逐字稿管理接口
│   │   ├── export.py                 # Word文档导出接口
│   │   ├── voiceprint.py             # 声纹管理接口
│   │   ├── speaker.py                # 说话人管理接口
│   │   ├── user.py                   # 用户管理接口
│   │   ├── file.py                   # 文件管理接口
│   │   ├── prompt.py                 # Prompt模板管理接口
│   │   ├── semantic_segmentation.py  # 语义分段模块
│   │   └── rag.py                    # RAG智能问答接口
│   ├── rag/                          # RAG检索增强生成模块
│   │   ├── agent.py                  # 智能会议助手Agent
│   │   ├── indexer.py                # 向量索引构建器
│   │   ├── retriever.py              # 向量检索器（含Reranker）
│   │   ├── vector_store.py           # ChromaDB向量存储
│   │   ├── embedding.py              # 文本向量化服务
│   │   └── config.py                 # RAG系统配置
│   ├── models.py                     # 数据模型定义
│   ├── urls.py                       # API路由配置
│   ├── utils.py                      # 通用工具函数
│   ├── auth_utils.py                 # 认证工具函数
│   ├── voiceprint_utils.py           # 声纹处理工具函数
│   ├── indexer_manager.py            # 索引管理器
│   ├── admin.py                      # Django后台管理
│   └── migrations/                   # 数据库迁移文件
├── asr_meeting_service/              # Django项目配置
│   ├── settings.py                   # 项目配置文件
│   ├── urls.py                       # 根路由配置
│   └── wsgi.py / asgi.py             # WSGI/ASGI入口
├── manage.py                         # Django管理命令
├── requirements_rag.txt              # RAG模块依赖
├── chroma_db/                        # ChromaDB向量数据库存储
├── uploaded_files/                   # 上传文件存储目录
├── temp_files/                       # 临时文件目录
└── media/                            # 媒体文件（头像、声纹音频等）
    ├── avatars/                      # 用户头像
    ├── speaker_avatars/              # 说话人头像
    ├── voiceprint_avatars/           # 声纹头像
    └── voiceprint_audio/             # 声纹音频文件
```

---

## 核心功能

### 1. 用户认证系统

| 功能 | 接口 | 说明 |
|------|------|------|
| 用户注册 | `POST /user/register` | 支持用户名、邮箱、密码注册 |
| 用户登录 | `POST /user/login` | Token认证，返回API令牌 |
| 用户登出 | `POST /user/logout` | 注销当前Token |
| 用户信息 | `GET /user/profile` | 获取/更新用户基本信息 |
| 头像上传 | `POST /user/avatar/upload` | 上传用户头像 |
| 头像删除 | `DELETE /user/avatar/delete` | 删除用户头像 |

**认证机制**: 基于 Django REST Framework 的 TokenAuthentication，支持 Bearer Token 格式。

---

### 2. ASR语音识别

基于 FunASR 框架，支持多说话人声纹识别，采用**两步法**：分离→切割→匹配。

**功能特性：**
- **语音转文字**: 基于 paraformer-zh 模型的中文语音识别
- **说话人分离**: cam++ 模型进行说话人日志（Speaker Diarization）
- **标点恢复**: ct-punc 模型自动添加标点符号
- **VAD语音活动检测**: fsmn-vad 模型检测有效语音段
- **声纹匹配两步法**: 
  1. FunASR 进行说话人分离 + ASR识别
  2. 对每个说话人切割音频片段，提取声纹特征，与用户声纹库匹配
- **多片段特征融合**: 取每个说话人TOP 3最长片段的特征平均值
- **自动声纹追加**: 匹配成功后自动将新声纹追加到说话人档案（最多保留4条）
- **热词支持**: 支持自定义热词（hotword）提高特定词汇识别率

**支持的音频格式**: `.wav`, `.mp3`, `.ogg`, `.flac`

---

### 3. 视频ASR

从视频文件中提取音频后进行语音识别。
- 使用 ffmpeg 从视频中提取16kHz单声道WAV音频
- 支持的视频格式: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

---

### 4. 会议纪要与摘要生成

| 功能 | 接口 | 说明 |
|------|------|------|
| 会议纪要生成 | `POST /generate_summary` | 生成结构化会议纪要（含议题、参与人、讨论内容、决议、待办事项） |
| 会议摘要生成 | `POST /meeting_abstract` | 生成轻量化摘要（支持short/medium/long三种长度） |
| 获取会议纪要 | `GET /meeting/summary/get` | 获取已生成的会议纪要 |
| 获取会议摘要 | `GET /meeting/abstract/get` | 获取已生成的会议摘要 |
| 编辑会议纪要 | `PUT /meeting/summary/update` | 用户手动编辑纪要内容 |
| 编辑会议摘要 | `PUT /meeting/abstract/update` | 用户手动编辑摘要内容 |
| 生成分段 | `POST /meeting/segments/generate` | 基于语义的会议分段 |
| 分段列表 | `GET /meeting/segments/list` | 获取分段列表 |
| 编辑分段 | `PUT /meeting/segments/update/<id>` | 编辑单个分段 |

**Prompt模板系统**:
- 支持默认模板和自定义模板
- 模板分为"纪要"和"摘要"两种类型
- 优先级：自定义Prompt > 模板Prompt > 默认Prompt
- 支持模板的增删改查和复制功能

---

### 5. 会议语义分段

**功能特点**:
1. **初分段**: 基于说话人切换和内容长度进行初步分段
2. **LLM优化**: 使用大语言模型为每个分段生成标题和核心总结
3. **批量处理**: 支持批量LLM调用优化，失败时回退到逐个处理
4. **容错机制**: LLM调用或解析失败时自动使用默认值

---

### 6. 会议多维度分析

**五大分析维度：**

| 分析类型 | 说明 |
|----------|------|
| **说话人分析** | 发言人列表、发言次数/时长、发言占比、角色判定（主导者/积极参与者/参与者/沉默参与者） |
| **会议概览** | 总时长、发言人数、平均发言时长、发言密度、会议效率评估 |
| **时间分布** | 发言热度时间轴、高峰时段识别、峰值时间定位 |
| **主题分析** | 会议主题提取、各主题讨论时长占比 |
| **决策分析** | 会议决策提取、行动项识别、跟进建议 |

---

### 7. 声纹识别系统

**功能特性：**
- **声纹提取**: 使用 campplus 模型提取192维声纹特征向量
- **声纹匹配**: 余弦相似度计算，动态阈值调整（说话人多时降低阈值）
- **一人多声纹**: 每个说话人支持多条声纹记录，取最高相似度匹配
- **自动声纹追加**: 会议中自动采集匹配到的说话人声纹（来源标注为"自动采集"）
- **声纹去重**: 自动声纹相似度≥96%时不重复添加
- **声纹数量控制**: 每个说话人最多保留4条声纹，优先保留最早手动注册的
- **重复检查**: 注册新声纹时检查是否与已有声纹重复

---

### 8. 说话人管理系统

**功能特性：**
- 说话人CRUD（增删改查）
- 说话人头像管理
- 说话人关联多条声纹
- 声纹来源区分：手动注册 / 会议自动采集

**数据模型关系**:
```
User (1) ──→ (N) Speaker (1) ──→ (N) Voiceprint
```

---

### 9. RAG智能问答系统

#### 模块架构

```
用户提问
   ↓
MeetingAgent (智能会议助手)
   ├─ LLM工具决策 → 判断是否需要调用工具
   ├─ 6种专业工具:
   │   ├─ SPEAKER_STATS    发言统计工具
   │   ├─ FULL_TRANSCRIPT  完整逐字稿工具
   │   ├─ SPEAKER_FILTER   发言人过滤工具
   │   ├─ TIME_RANGE_QUERY 时间范围查询工具
   │   ├─ KEYWORD_SEARCH   关键词搜索工具
   │   └─ SEGMENT_RETRIEVER 分段检索工具
   ├─ Retriever (向量检索)
   │   ├─ VectorStore (ChromaDB)
   │   └─ EmbeddingService (BGE模型)
   └─ LLM生成回答 → 返回(answer, sources, thinking)
```

#### 核心组件

| 组件 | 说明 |
|------|------|
| **Agent** | 智能对话助手，工具调用决策，多轮对话 |
| **Indexer** | 会议数据索引构建，语义分块 |
| **Retriever** | 向量检索 + 可选Reranker重排 |
| **VectorStore** | ChromaDB封装，单例模式 |
| **EmbeddingService** | BGE中文Embedding模型，懒加载 |
| **Config** | RAG系统所有配置参数 |

#### 索引数据类型

- 逐字稿（transcript）- 语义分块
- 会议纪要（summary）
- 会议摘要（abstract）
- 会议分段内容（segment）
- 分段摘要（segment_summary）

#### RAG API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/rag/chat` | POST | 智能问答聊天 |
| `/rag/index` | POST | 索引会议文件 |
| `/rag/status` | GET | 获取索引状态 |
| `/rag/test` | GET | 测试检索功能 |

---

### 10. 文件管理系统

**功能特性：**
- 文件上传（音频/视频）
- 文件列表查询
- 文件重命名
- 文件删除
- 文件下载
- 文件状态追踪（original/processed）

---

### 11. 逐字稿管理

**功能特性：**
- 逐字稿搜索
- 逐字稿获取
- 逐字稿编辑
- 逐字稿生成（从ASR结果生成格式化文本）

---

### 12. Word文档导出

**支持导出类型：**
- 逐字稿导出（含说话人、时间戳）
- 会议纪要导出
- 会议摘要导出

**文档格式**: 使用 python-docx 库生成 .docx 文件，包含标题、生成时间、格式化正文。

---

## 数据模型

| 模型 | 说明 | 主要字段 |
|------|------|----------|
| **User** | 用户模型（扩展Django User） | email, avatar, created_at, updated_at |
| **UploadedFile** | 上传文件 | user, original_name, stored_name, file_path, file_type(audio/video), file_size, status, meeting_type |
| **Transcription** | 转录记录 | file(一对一), transcription_text, segments(JSON) |
| **MeetingSummary** | 会议纪要 | file(一对一), summary_text, abstract_text, is_customized |
| **MeetingSegment** | 会议分段 | file, user, segment_index, start_time, end_time, title, content, summary, is_edited |
| **Speaker** | 说话人 | user, name, avatar |
| **Voiceprint** | 声纹信息 | speaker, user, feature(二进制), audio_file, source_type(manual/auto), source_meeting |
| **Prompt** | Prompt模板 | user, name, system_prompt, user_prompt, category(default/custom), template_type(summary/abstract) |
| **AudioRecord** | 音频记录（兼容旧版） | filename, file_size, transcription, summary |

---

## API接口

共 **30+** 个API接口，分为以下类别：

| 类别 | 接口数量 |
|------|----------|
| 基础接口 | 1（健康检查） |
| ASR接口 | 2（音频ASR、视频ASR） |
| 会议纪要/摘要 | 8（生成、获取、编辑、分段） |
| 会议分析 | 1（多维度分析） |
| Word导出 | 3（逐字稿、纪要、摘要） |
| 声纹管理 | 7 |
| 说话人管理 | 9 |
| 用户管理 | 6 |
| 文件管理 | 5 |
| 逐字稿管理 | 4 |
| Prompt模板 | 5 |
| RAG智能问答 | 4 |

完整接口定义见 [asr_api/urls.py](file:///f:/University-graduate-Item/FunASR-Meeting-Item/asr-backend/asr_meeting_service/asr_api/urls.py)。

---

## 快速启动

### 环境要求

- Python 3.10+
- ffmpeg（音频处理依赖）
- 足够的内存（加载AI模型需要）

### 安装步骤

```bash
# 1. 进入项目目录
cd asr-backend/asr_meeting_service

# 2. 安装基础依赖
pip install django djangorestframework django-cors-headers python-docx ffmpeg-python funasr modelscope openai

# 3. 安装RAG模块依赖
pip install -r requirements_rag.txt

# 如果网络慢，可以用国内源：
# pip install -r requirements_rag.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 5. 初始化Prompt模板
python manage.py init_prompt_templates

# 6. 创建超级用户（可选）
python manage.py createsuperuser

# 7. 启动服务
python manage.py runserver 0.0.0.0:8000
```

### 访问地址

- **API服务**: http://localhost:8000/
- **Django管理后台**: http://localhost:8000/admin/
- **健康检查**: http://localhost:8000/

### 配置说明

主要配置在 [settings.py](file:///f:/University-graduate-Item/FunASR-Meeting-Item/asr-backend/asr_meeting_service/asr_meeting_service/settings.py) 中：

- `LLM_CONFIG`: 大语言模型API配置
- `ALLOWED_EXTENSIONS`: 支持的音频格式
- `ALLOWED_VIDEO_EXTENSIONS`: 支持的视频格式
- `FILE_UPLOAD_DIR`: 文件上传目录
- `TEMP_DIR`: 临时文件目录
- `VOICEPRINT_DIR`: 声纹文件目录

---

## 技术亮点

1. **两步法声纹识别**: 先FunASR分离说话人，再切割音频提取声纹匹配，准确率更高
2. **多片段特征平均**: 取TOP 3最长片段特征平均，减少单片段噪声影响
3. **动态阈值调整**: 根据说话人数量动态调整声纹匹配阈值
4. **LLM工具调用Agent**: 智能判断问题类型，选择最优工具处理
5. **语义分块索引**: 按句子边界智能切分文本，保持语义完整性
6. **离线Embedding**: BGE模型本地运行，保护数据隐私
7. **容错降级机制**: LLM调用失败时有完整的回退方案
8. **一人多声纹**: 支持多条声纹，自动追加和去重
9. **单例懒加载**: AI模型采用单例模式和懒加载，节省内存资源
10. **完整的数据权限隔离**: 所有用户数据严格按用户ID隔离

---

## 许可证

本项目仅供学习和研究使用。
