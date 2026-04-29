# ==========================================
# RAG配置
# ==========================================
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
    """RAG系统配置"""

    # ========== ChromaDB配置 ==========
    CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")
    CHROMA_COLLECTION_NAME = "meeting_embeddings"

    # ========== Embedding模型配置 ==========
    EMBEDDING_MODEL_NAME = "BAAI/bge-base-zh-v1.5"  # 轻量版
    # EMBEDDING_MODEL_NAME = "BAAI/bge-m3"  # 完整版
    EMBEDDING_DEVICE = "cpu"  # 如果你有GPU可以改"cuda"

    # ========== Reranker模型配置 ==========
    RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"  # 轻量版
    # RERANKER_MODEL_NAME = "BAAI/bge-reranker-large"  # 完整版
    USE_RERANKER = False  # 暂时禁用Reranker，避免兼容性问题
    RERANKER_TOP_K = 3  # 重排后保留的数量

    # ========== 检索配置 ==========
    VECTOR_SEARCH_TOP_K = 10  # 向量检索初筛数量
    SIMILARITY_THRESHOLD = 0.5  # 相似度阈值

    # ========== 分块配置 ==========
    CHUNK_SIZE = 512  # 分块大小（字符）
    CHUNK_OVERLAP = 50  # 重叠大小（字符）

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

    # ========== 聊天历史配置 ==========
    MAX_HISTORY_LENGTH = 10  # 保留的历史轮数


# 确保ChromaDB目录存在
if not os.path.exists(RAGConfig.CHROMA_PERSIST_DIR):
    os.makedirs(RAGConfig.CHROMA_PERSIST_DIR)
    print(f"✅ 创建ChromaDB目录: {RAGConfig.CHROMA_PERSIST_DIR}")

