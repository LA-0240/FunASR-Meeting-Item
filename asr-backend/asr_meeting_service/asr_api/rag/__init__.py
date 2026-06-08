# ==========================================
# FunASR智能会议纪要系统 - RAG模块初始化
# ==========================================
"""
RAG（检索增强生成）模块包
========================

本模块实现了会议记录的智能检索和问答功能，包括：

主要组件：
    - RAGConfig: 配置管理类，管理RAG系统的所有配置参数
    - EmbeddingService: 文本向量化服务，使用BGE模型将文本转换为向量
    - VectorStore: ChromaDB向量存储管理，负责向量的存储和检索
    - Retriever: 检索器，结合向量检索和Reranker重排序
    - Indexer: 索引器，负责将会议记录数据索引到向量数据库
    - MeetingAgent: 会议助手Agent，提供智能对话问答功能

使用方式：
    from asr_api.rag import MeetingAgent, Indexer
    # 创建索引
    Indexer.index_file(file_id=1)
    # 问答对话
    agent = MeetingAgent(user_id=1, file_id=1)
    result = agent.chat("会议主要讨论了什么？")

注意事项：
    - 本模块强制使用离线模式，避免网络请求
    - 需要预先下载并缓存相关模型文件到 hf_cache 目录
    - 向量数据持久化存储在 chroma_db 目录
"""
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

