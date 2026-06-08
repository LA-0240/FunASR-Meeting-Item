# ==========================================
# RAG配置管理
# ==========================================
"""
RAG系统配置文件
================

本文件定义了RAG（检索增强生成）系统的所有配置参数，包括：

配置分类：
    - ChromaDB配置: 向量数据库存储路径和集合名称
    - Embedding模型配置: 文本向量化模型相关参数
    - Reranker模型配置: 重排序模型相关参数
    - 检索配置: 向量搜索和相似度匹配的参数
    - 分块配置: 文本分块的大小和重叠度
    - LLM配置: 大语言模型的API配置
    - Agent配置: 对话助手的系统提示词和历史记录管理

使用方式：
    from asr_api.rag.config import RAGConfig
    # 获取配置
    embedding_model = RAGConfig.EMBEDDING_MODEL_NAME
    # 修改配置（不推荐运行时修改）
    RAGConfig.CHUNK_SIZE = 1024

注意事项：
    - 配置在模块加载时初始化，运行时修改可能不生效
    - GPU配置需要根据实际硬件环境调整
    - 离线模式下需要确保模型文件已缓存
"""
import os
from pathlib import Path

# ！！！强制全局离线模式 —— 彻底根治联网超时问题！！！
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
print("🔒 已强制开启离线模式 —— 禁止所有网络请求！")

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ========== 设置HuggingFace缓存目录 ==========
HF_CACHE_DIR = os.path.join(BASE_DIR, "hf_cache")
if not os.path.exists(HF_CACHE_DIR):
    os.makedirs(HF_CACHE_DIR)
    print(f"✅ 创建HuggingFace缓存目录: {HF_CACHE_DIR}")
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = HF_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ========== 设置清华镜像源（国内加速，仅在需要下载时使用）==========
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
print(f"🌐 使用镜像源: {os.environ['HF_ENDPOINT']}")


class RAGConfig:
    """
    RAG系统配置类
    
    包含RAG系统运行所需的所有配置参数，分为以下几个类别：
    - ChromaDB向量数据库配置
    - Embedding向量化模型配置
    - Reranker重排序模型配置
    - 检索和相似度匹配配置
    - 文本分块配置
    - LLM大语言模型配置
    - Agent对话助手配置
    """

    # ========== ChromaDB配置 ==========
    CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")
    """ChromaDB向量数据库持久化存储目录"""
    
    CHROMA_COLLECTION_NAME = "meeting_embeddings"
    """ChromaDB中存储会议向量的集合名称"""

    # ========== Embedding模型配置 ==========
    EMBEDDING_MODEL_NAME = "BAAI/bge-base-zh-v1.5"  # 轻量版
    """Embedding模型名称，使用BGE中文轻量版"""
    
    # EMBEDDING_MODEL_NAME = "BAAI/bge-m3"  # 完整版
    """Embedding模型完整版（注释中备用）"""
    
    EMBEDDING_DEVICE = "cpu"  # 如果你有GPU可以改"cuda"
    """Embedding模型运行设备，cpu/cuda"""

    # ========== Reranker模型配置 ==========
    RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"  # 轻量版
    """Reranker重排序模型名称，使用轻量版"""
    
    # RERANKER_MODEL_NAME = "BAAI/bge-reranker-large"  # 完整版
    """Reranker重排序模型完整版（注释中备用）"""
    
    USE_RERANKER = False  # 暂时禁用Reranker，避免兼容性问题
    """是否使用Reranker重排序，暂时禁用"""
    
    RERANKER_TOP_K = 3  # 重排后保留的数量
    """Reranker重排序后返回的结果数量"""

    # ========== 检索配置 ==========
    VECTOR_SEARCH_TOP_K = 10  # 向量检索初筛数量
    """向量相似度搜索初筛返回的结果数量"""
    
    SIMILARITY_THRESHOLD = 0.5  # 相似度阈值
    """向量相似度阈值，低于此值的结果被过滤"""

    # ========== 分块配置 ==========
    CHUNK_SIZE = 512  # 分块大小（字符）
    """文本分块的最大字符数"""
    
    CHUNK_OVERLAP = 50  # 重叠大小（字符）
    """相邻文本块之间的重叠字符数，保持语义连续性"""

    # ========== LLM配置（复用现有配置）==========
    from django.conf import settings
    if hasattr(settings, 'LLM_CONFIG'):
        LLM_CONFIG = settings.LLM_CONFIG
    else:
        LLM_CONFIG = {
            "api_key": "ms-74ceb98c-5801-46ae-90c3-e5e5bb9bb886",
            "base_url": "https://api-inference.modelscope.cn/v1/",
            "model_name": "Qwen/Qwen3.5-35B-A3B"
        }
    """大语言模型API配置，优先使用Django settings配置"""

    # ========== Agent配置 ==========
    AGENT_SYSTEM_PROMPT = """你是一个专业的会议助手，可以帮助用户查询和分析会议记录。

请始终遵循以下规则：
1. 回答要基于检索到的会议内容，不要编造
2. 回答要清晰、有条理，使用 Markdown 格式输出
3. 合理使用标题、列表、加粗等格式增强可读性
4. ⚠️ 不要在回答内容里自己生成"引用来源"部分，系统会在下方统一展示
5. 如果信息不足，如实告知用户
6. 使用中文回答

Markdown 格式要求：
- 重要标题使用 ## 或 ###
- 列表使用 - 或 1. 2. 3.
- 重要内容使用 **加粗**
- 代码或关键短语使用 `反引号`
"""
    """对话助手的系统提示词，定义助手的行为规范"""

    # ========== 聊天历史配置 ==========
    MAX_HISTORY_LENGTH = 10  # 保留的历史轮数
    """对话历史记录的最大保留轮数"""


# 确保ChromaDB目录存在
if not os.path.exists(RAGConfig.CHROMA_PERSIST_DIR):
    os.makedirs(RAGConfig.CHROMA_PERSIST_DIR)
    print(f"✅ 创建ChromaDB目录: {RAGConfig.CHROMA_PERSIST_DIR}")

