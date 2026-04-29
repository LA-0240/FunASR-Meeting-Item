# ==========================================
# ChromaDB向量存储服务
# ==========================================
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import numpy as np
from .config import RAGConfig
from .embedding import EmbeddingService


class VectorStore:
    """ChromaDB向量存储管理"""

    _instance = None
    _client = None
    _collection = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _init_client(cls):
        """初始化ChromaDB客户端"""
        if cls._client is None:
            print(f"📥 正在初始化ChromaDB: {RAGConfig.CHROMA_PERSIST_DIR}...")
            cls._client = chromadb.PersistentClient(
                path=RAGConfig.CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
            cls._get_or_create_collection()
            print("✅ ChromaDB初始化成功!")

    @classmethod
    def _get_or_create_collection(cls):
        """获取或创建集合"""
        if cls._collection is None:
            try:
                cls._collection = cls._client.get_collection(
                    name=RAGConfig.CHROMA_COLLECTION_NAME
                )
                print(f"✅ 加载现有集合: {RAGConfig.CHROMA_COLLECTION_NAME}")
            except Exception:
                cls._collection = cls._client.create_collection(
                    name=RAGConfig.CHROMA_COLLECTION_NAME,
                    metadata={"description": "会议记录向量存储"}
                )
                print(f"✅ 创建新集合: {RAGConfig.CHROMA_COLLECTION_NAME}")

    @classmethod
    def add_documents(
        cls,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        """
        添加文档到向量数据库

        Args:
            documents: 文档文本列表
            metadatas: 元数据列表
            ids: 文档ID列表（可选，自动生成）
        """
        cls._init_client()

        # 生成ID（如果没有提供）
        if ids is None:
            from uuid import uuid4
            ids = [str(uuid4()) for _ in range(len(documents))]

        # 生成向量
        embeddings = EmbeddingService.embed_documents(documents)

        # 转换为列表格式（ChromaDB需要）
        embeddings_list = [emb.tolist() for emb in embeddings]

        # 添加到ChromaDB
        cls._collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings_list
        )
        print(f"✅ 已添加 {len(documents)} 个文档块")

    @classmethod
    def similarity_search(
        cls,
        query: str,
        file_id: Optional[int] = None,
        user_id: Optional[int] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索

        Args:
            query: 查询文本
            file_id: 按文件过滤（可选）
            user_id: 按用户过滤（可选）
            top_k: 返回数量（默认用配置）

        Returns:
            搜索结果列表
        """
        if top_k is None:
            top_k = RAGConfig.VECTOR_SEARCH_TOP_K

        cls._init_client()

        # 生成查询向量
        query_embedding = EmbeddingService.embed_text(query).tolist()

        # 构建查询条件
        where_clause = {}
        if file_id is not None:
            where_clause["file_id"] = file_id
        if user_id is not None:
            where_clause["user_id"] = user_id

        # 执行搜索
        if where_clause:
            results = cls._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause
            )
        else:
            results = cls._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

        # 格式化输出
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "similarity": 1 - results["distances"][0][i]  # 转换为相似度
            })

        return formatted_results

    @classmethod
    def delete_by_file_id(cls, file_id: int):
        """删除指定文件的所有向量"""
        cls._init_client()
        try:
            cls._collection.delete(where={"file_id": file_id})
            print(f"✅ 已删除文件ID={file_id} 的所有向量")
        except Exception as e:
            print(f"⚠️ 删除向量时出错: {e}")

    @classmethod
    def delete_by_user_id(cls, user_id: int):
        """删除指定用户的所有向量"""
        cls._init_client()
        try:
            cls._collection.delete(where={"user_id": user_id})
            print(f"✅ 已删除用户ID={user_id} 的所有向量")
        except Exception as e:
            print(f"⚠️ 删除向量时出错: {e}")

    @classmethod
    def count(cls) -> int:
        """获取文档总数"""
        cls._init_client()
        return cls._collection.count()

    @classmethod
    def count_by_file_id(cls, file_id: int) -> int:
        """获取指定文件的文档数量"""
        cls._init_client()
        try:
            results = cls._collection.get(where={"file_id": file_id})
            return len(results["ids"])
        except Exception as e:
            print(f"⚠️ 统计文件向量时出错: {e}")
            return 0

    @classmethod
    def is_indexed(cls, file_id: int) -> bool:
        """检查文件是否已索引"""
        return cls.count_by_file_id(file_id) > 0

    @classmethod
    def get_file_info(cls, file_id: int) -> Dict[str, Any]:
        """获取文件索引详情"""
        count = cls.count_by_file_id(file_id)
        return {
            "file_id": file_id,
            "indexed": count > 0,
            "chunk_count": count
        }

    @classmethod
    def reset(cls):
        """清空集合（谨慎使用！）"""
        cls._init_client()
        try:
            cls._client.delete_collection(RAGConfig.CHROMA_COLLECTION_NAME)
            cls._collection = None
            cls._get_or_create_collection()
            print("✅ 向量数据库已清空")
        except Exception as e:
            print(f"⚠️ 清空数据库时出错: {e}")
