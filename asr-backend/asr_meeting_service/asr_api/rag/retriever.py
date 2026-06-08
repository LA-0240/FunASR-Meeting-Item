# ==========================================
# 检索器 - 带Reranker版本
# ==========================================
"""
会议记录检索器模块
===================

本模块实现了向量检索和重排的完整流程，为RAG系统提供高质量的相关文档检索。

主要功能：
    - 向量检索：使用Embedding进行相似度初筛
    - 重排序：使用Reranker对初筛结果进行精细排序
    - 结果格式化：将检索结果格式化为LLM可读的上下文

检索流程：
    1. 用户查询向量化
    2. 向量数据库相似度搜索（初筛）
    3. Reranker重排序（可选，默认禁用）
    4. 返回Top K结果

核心类：
    Retriever: 会议记录检索器类

使用方式：
    from asr_api.rag import Retriever
    # 搜索相关内容
    results = Retriever.search("会议的主要议题", file_id=1)
    # 格式化为上下文
    context = Retriever.format_context(results)

注意事项：
    - 默认禁用Reranker以提高性能和兼容性
    - 可在配置中启用USE_RERANKER使用重排序功能
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# ！！！第一时间强制离线模式！！！
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# ！！！关键：在导入任何模型前设置环境变量！！！
BASE_DIR = Path(__file__).resolve().parent.parent.parent
HF_CACHE_DIR = os.path.join(BASE_DIR, "hf_cache")
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = HF_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 使用清华镜像源！！
print("🔒 已强制开启离线模式 —— 禁止所有网络请求！")

# ！！！这里才导入配置！！！
from .config import RAGConfig
from .vector_store import VectorStore


class Retriever:
    """
    会议记录检索器类
    
    负责执行完整的检索流程，包括向量初筛和可选的Reranker重排。
    同时提供结果格式化功能，便于LLM使用。
    
    核心特性：
        - 支持按文件和用户过滤
        - 可选的Reranker重排序（默认禁用）
        - 灵活的结果格式化
    
    Attributes:
        _reranker: Reranker模型实例（懒加载）
    """

    _reranker = None

    @classmethod
    def _load_reranker(cls):
        """
        加载Reranker模型（懒加载）
        
        仅在USE_RERANKER配置为True且首次调用时加载模型。
        如果加载失败，会自动禁用重排功能。
        
        注意：目前默认禁用，加载失败不影响主流程。
        """
        if cls._reranker is None and RAGConfig.USE_RERANKER:
            print(f"📥 正在加载Reranker: {RAGConfig.RERANKER_MODEL_NAME}...")
            try:
                from FlagEmbedding import FlagReranker
                # 先使用最基本的初始化方式
                cls._reranker = FlagReranker(
                    RAGConfig.RERANKER_MODEL_NAME
                )
                print(f"✅ Reranker加载成功!")
            except Exception as e:
                print(f"❌ Reranker加载失败: {e}")
                import traceback
                traceback.print_exc()
                print(f"⚠️ 将不使用重排功能，直接用相似度分数")
                RAGConfig.USE_RERANKER = False

    @classmethod
    def _rerank(cls, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用Reranker进行重排序
        
        对向量检索的初筛结果进行精细排序，提高检索质量。
        
        Args:
            query: 查询文本
            results: 向量检索的初筛结果列表

        Returns:
            List[Dict[str, Any]]: 重排序后的结果列表（Top K）
        """
        if not RAGConfig.USE_RERANKER or not results:
            return results[:RAGConfig.RERANKER_TOP_K]

        cls._load_reranker()
        if cls._reranker is None:
            return results[:RAGConfig.RERANKER_TOP_K]

        # 构建查询-文档对
        pairs = [[query, r["document"]] for r in results]

        # 计算分数
        scores = cls._reranker.compute_score(pairs, normalize=True)

        # 合并分数并排序
        for i, result in enumerate(results):
            result["rerank_score"] = float(scores[i])

        # 按重排分数降序排序
        results_sorted = sorted(
            results,
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        print(f"✅ 重排完成!")

        # 返回Top K
        return results_sorted[:RAGConfig.RERANKER_TOP_K]

    @classmethod
    def search(
        cls,
        query: str,
        file_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        完整检索流程：向量检索 → (可选) Reranker重排
        
        执行完整的检索流程，先进行向量相似度搜索初筛，
        再（可选）使用Reranker进行精细重排。
        
        Args:
            query: 查询文本
            file_id: 按文件ID过滤（可选）
            user_id: 按用户ID过滤（可选）

        Returns:
            List[Dict[str, Any]]: 检索结果列表，每个结果包含：
                - id: 文档ID
                - document: 文档内容
                - metadata: 元数据
                - similarity: 相似度分数（或rerank_score）
                
        Examples:
            >>> results = Retriever.search("会议决议", file_id=1)
            >>> for r in results:
            ...     print(r["similarity"], r["document"])
        """
        print(f"🔍 检索: {query[:50]}...")

        # 1. 向量检索（初筛）
        results = VectorStore.similarity_search(
            query=query,
            file_id=file_id,
            user_id=user_id
        )

        if not results:
            print("⚠️ 未找到相关内容")
            return []

        print(f"✅ 初筛: {len(results)} 个结果")

        # 2. 重排
        results_reranked = cls._rerank(query, results)
        print(f"✅ 最终: {len(results_reranked)} 个结果")

        return results_reranked

    @classmethod
    def format_context(cls, results: List[Dict[str, Any]]) -> str:
        """
        格式化检索结果为LLM可读的上下文文本
        
        将检索结果列表格式化为结构化的文本，包含来源信息和内容，
        便于LLM理解和使用。
        
        Args:
            results: 检索结果列表

        Returns:
            str: 格式化后的上下文文本
            
        Examples:
            >>> context = Retriever.format_context(results)
            >>> print(context)
            [逐字稿 00:00-01:30 (相关度: 0.892)]
            会议内容...
        """
        if not results:
            return ""

        context_parts = []

        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            doc_info = []

            # 构建来源信息
            data_type = metadata.get("data_type", "unknown")
            data_type_names = {
                "transcript": "逐字稿",
                "summary": "会议纪要",
                "abstract": "会议摘要",
                "segment_summary": "分段摘要",
                "segment": "会议分段"
            }
            type_name = data_type_names.get(data_type, data_type)

            doc_info.append(f"[{type_name}")

            if metadata.get("segment_index") is not None:
                doc_info.append(f" 分段{metadata['segment_index']}")

            if metadata.get("start_time") is not None and metadata.get("end_time") is not None:
                start = cls._format_time(metadata["start_time"])
                end = cls._format_time(metadata["end_time"])
                doc_info.append(f" {start}-{end}")

            if metadata.get("title"):
                doc_info.append(f" {metadata['title']}")

            doc_info.append("]")

            # 添加分数
            score = result.get("rerank_score", result.get("similarity"))
            if score:
                doc_info.append(f" (相关度: {score:.3f})")

            # 添加内容
            context_parts.append(f"{''.join(doc_info)}\n{result['document']}\n")

        return "\n".join(context_parts)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        格式化秒数为 MM:SS 时间格式
        
        Args:
            seconds: 秒数

        Returns:
            str: MM:SS格式的时间字符串
            
        Examples:
            >>> Retriever._format_time(90)
            '01:30'
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

