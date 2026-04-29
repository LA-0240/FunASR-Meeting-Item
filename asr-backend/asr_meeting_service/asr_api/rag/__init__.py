# ==========================================
# FunASR智能会议纪要系统 - RAG模块
# ==========================================
import os
from pathlib import Path

# ！！！第一时间强制离线模式！！！
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
print("🔒 已强制开启离线模式 —— 禁止所有网络请求！")

# ！！！然后设置环境变量！！！
BASE_DIR = Path(__file__).resolve().parent.parent.parent
HF_CACHE_DIR = os.path.join(BASE_DIR, "hf_cache")
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = HF_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 使用清华镜像源！！

# 现在才导入模块
from .config import RAGConfig
from .embedding import EmbeddingService
from .vector_store import VectorStore
from .retriever import Retriever
from .indexer import Indexer
from .agent import MeetingAgent

__all__ = [
    'RAGConfig',
    'EmbeddingService',
    'VectorStore',
    'Retriever',
    'Indexer',
    'MeetingAgent',
]

