# ==========================================
# 检索器 - 带Reranker版本
# ==========================================
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
    """会议记录检索器"""

    _reranker = None

    @classmethod
    def _load_reranker(cls):
        """加载重排器（懒加载）"""
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
        使用Reranker重排

        Args:
            query: 查询文本
            results: 初筛结果

        Returns:
            重排后的结果
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
        完整检索流程：向量检索 → Reranker

        Args:
            query: 查询文本
            file_id: 按文件过滤
            user_id: 按用户过滤

        Returns:
            最终检索结果
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
        格式化检索结果为上下文字符串

        Args:
            results: 检索结果

        Returns:
            格式化的上下文文本
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
        """格式化秒数为 MM:SS 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

