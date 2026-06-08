# ==========================================
# ChromaDB向量存储服务
# ==========================================
"""
向量数据库存储服务
==================

本模块封装了ChromaDB向量数据库的操作，提供向量的存储、检索、删除等功能。

主要功能：
    - 添加文档: 将文本和元数据添加到向量数据库
    - 相似度搜索: 根据查询文本检索相关文档
    - 删除数据: 按文件ID或用户ID删除向量
    - 统计查询: 获取文档数量等统计信息
    - 索引检查: 检查文件是否已索引

核心类：
    VectorStore: ChromaDB向量存储管理类

使用方式：
    from asr_api.rag import VectorStore
    # 添加文档
    VectorStore.add_documents(["文本1", "文本2"], [{"file_id": 1}, {"file_id": 1}])
    # 搜索
    results = VectorStore.similarity_search("查询文本", file_id=1)

注意事项：
    - 首次使用时会初始化ChromaDB客户端
    - 数据持久化存储在配置的目录中
    - 支持按文件ID和用户ID过滤搜索结果
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import numpy as np
from .config import RAGConfig
from .embedding import EmbeddingService


class VectorStore:
    """
    ChromaDB向量存储管理类
    
    采用单例模式管理ChromaDB客户端和集合，提供向量的增删改查功能。
    
    主要功能：
        - 文档添加: 将文本向量化后存入数据库
        - 相似度搜索: 根据查询文本检索相关文档
        - 数据删除: 按条件删除向量数据
        - 统计查询: 获取索引状态和数量信息
        
    Attributes:
        _instance: 单例实例
        _client: ChromaDB持久化客户端
        _collection: 向量集合对象
    """

    _instance = None
    """单例实例"""
    
    _client = None
    """ChromaDB持久化客户端"""
    
    _collection = None
    """向量集合对象"""

    def __new__(cls):
        """
        单例模式构造函数
        
        Returns:
            VectorStore: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _init_client(cls):
        """
        初始化ChromaDB客户端（懒加载）
        
        首次调用时初始化ChromaDB持久化客户端，后续调用直接使用已初始化的客户端。
        同时会获取或创建指定的集合。
        """
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
        """
        获取或创建向量集合
        
        尝试获取已存在的集合，如果不存在则创建新的集合。
        """
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
        
        将文档文本自动向量化后存入ChromaDB，同时保存元数据。
        
        Args:
            documents: 文档文本列表
            metadatas: 元数据列表（与documents一一对应）
            ids: 文档ID列表（可选，不提供时自动生成UUID）
            
        Examples:
            >>> VectorStore.add_documents(
            ...     ["文本1", "文本2"],
            ...     [{"file_id": 1, "data_type": "transcript"}, {"file_id": 1, "data_type": "summary"}]
            ... )
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
        
        根据查询文本检索最相似的文档，支持按文件ID或用户ID过滤。
        
        Args:
            query: 查询文本
            file_id: 按文件ID过滤（可选）
            user_id: 按用户ID过滤（可选）
            top_k: 返回结果数量（默认使用配置中的VECTOR_SEARCH_TOP_K）

        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含：
                - id: 文档ID
                - document: 文档内容
                - metadata: 元数据
                - distance: 距离值（越小越相似）
                - similarity: 相似度值（1 - distance，越大越相似）
                
        Examples:
            >>> results = VectorStore.similarity_search("会议要点", file_id=1)
            >>> for r in results:
            ...     print(r["document"], r["similarity"])
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
        """
        删除指定文件的所有向量
        
        Args:
            file_id: 文件ID
        """
        cls._init_client()
        try:
            cls._collection.delete(where={"file_id": file_id})
            print(f"✅ 已删除文件ID={file_id} 的所有向量")
        except Exception as e:
            print(f"⚠️ 删除向量时出错: {e}")

    @classmethod
    def delete_by_user_id(cls, user_id: int):
        """
        删除指定用户的所有向量
        
        Args:
            user_id: 用户ID
        """
        cls._init_client()
        try:
            cls._collection.delete(where={"user_id": user_id})
            print(f"✅ 已删除用户ID={user_id} 的所有向量")
        except Exception as e:
            print(f"⚠️ 删除向量时出错: {e}")

    @classmethod
    def count(cls) -> int:
        """
        获取向量数据库中文档总数
        
        Returns:
            int: 文档总数
        """
        cls._init_client()
        return cls._collection.count()

    @classmethod
    def count_by_file_id(cls, file_id: int) -> int:
        """
        获取指定文件的文档数量
        
        Args:
            file_id: 文件ID
            
        Returns:
            int: 该文件索引的文档块数量
        """
        cls._init_client()
        try:
            results = cls._collection.get(where={"file_id": file_id})
            return len(results["ids"])
        except Exception as e:
            print(f"⚠️ 统计文件向量时出错: {e}")
            return 0

    @classmethod
    def is_indexed(cls, file_id: int) -> bool:
        """
        检查文件是否已索引
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否已索引（数量>0返回True）
        """
        return cls.count_by_file_id(file_id) > 0

    @classmethod
    def get_file_info(cls, file_id: int) -> Dict[str, Any]:
        """
        获取文件索引详情
        
        Args:
            file_id: 文件ID
            
        Returns:
            Dict[str, Any]: 文件索引信息，包含：
                - file_id: 文件ID
                - indexed: 是否已索引
                - chunk_count: 文档块数量
        """
        count = cls.count_by_file_id(file_id)
        return {
            "file_id": file_id,
            "indexed": count > 0,
            "chunk_count": count
        }

    @classmethod
    def reset(cls):
        """
        清空集合（谨慎使用！）
        
        删除并重建整个集合，所有数据将永久丢失！
        """
        cls._init_client()
        try:
            cls._client.delete_collection(RAGConfig.CHROMA_COLLECTION_NAME)
            cls._collection = None
            cls._get_or_create_collection()
            print("✅ 向量数据库已清空")
        except Exception as e:
            print(f"⚠️ 清空数据库时出错: {e}")
