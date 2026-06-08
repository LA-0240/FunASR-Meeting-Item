# ==========================================
# Embedding服务 - HuggingFace版本
# ==========================================
"""
文本向量化服务
==============

本模块实现了文本到向量的转换功能，使用BGE（BAAI General Embedding）模型将文本转换为高维向量表示。

主要功能：
    - 单文本向量化: 将单个文本转换为向量
    - 批量文本向量化: 一次处理多个文本提高效率
    - 模型懒加载: 首次使用时才加载模型，节省内存
    - 单例模式: 全局唯一实例，避免重复加载

核心类：
    EmbeddingService: 文本向量化服务类

使用方式：
    from asr_api.rag import EmbeddingService
    # 单文本向量化
    vector = EmbeddingService.embed_text("你好，世界")
    # 批量向量化
    vectors = EmbeddingService.embed_documents(["文本1", "文本2"])

注意事项：
    - 首次使用时会加载模型，需要一定时间
    - 模型使用CPU运行，确保有足够内存
    - 离线模式，模型需要预先缓存
"""
import os
import numpy as np
from typing import List, Union
from pathlib import Path

# ！！！第一时间强制离线模式！！！
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# ！！！关键：在导入任何transformers前设置环境变量！！！
BASE_DIR = Path(__file__).resolve().parent.parent.parent
HF_CACHE_DIR = os.path.join(BASE_DIR, "hf_cache")
if not os.path.exists(HF_CACHE_DIR):
    os.makedirs(HF_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = HF_CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = HF_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 使用清华镜像源！！
print("🔒 已强制开启离线模式 —— 禁止所有网络请求！")
print(f"✅ HuggingFace缓存目录: {HF_CACHE_DIR}")

# ！！！解决 meta tensor 问题：设置 PyTorch 相关环境变量！！！
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ！！！这里才导入配置（确保环境变量先设置好！！！
from .config import RAGConfig


class EmbeddingService:
    """
    文本向量化服务类（使用BGE模型）
    
    采用单例模式和懒加载策略，避免重复加载模型，节省内存资源。
    
    主要特性：
        - 单例模式: 全局唯一实例
        - 懒加载: 首次使用时才加载模型
        - 线程安全: 防止并发加载问题
        - 批量处理: 支持单个和批量文本向量化
        
    Attributes:
        _instance: 单例实例
        _model: 加载的Embedding模型
        _model_loading: 模型加载中标志位
    """

    _instance = None
    """单例实例"""
    
    _model = None
    """加载的Embedding模型"""
    
    _model_loading = False
    """防止并发加载的标志位"""

    def __new__(cls):
        """
        单例模式构造函数 - 避免重复加载模型
        
        Returns:
            EmbeddingService: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _load_model(cls):
        """
        加载Embedding模型（懒加载方式）
        
        首次调用时才加载模型，后续调用直接使用已加载的模型。
        使用CPU强制运行，避免GPU兼容性问题。
        
        Raises:
            Exception: 模型加载失败时抛出异常
        """
        if cls._model is not None:
            return
            
        if cls._model_loading:
            # 等待其他线程加载完成
            import time
            wait_count = 0
            while cls._model_loading and wait_count < 30:
                time.sleep(0.5)
                wait_count += 1
            if cls._model is not None:
                return
                
        cls._model_loading = True
        
        try:
            print(f"📥 正在加载Embedding模型: {RAGConfig.EMBEDDING_MODEL_NAME}...")
            
            # 方案：使用 sentence-transformers，显式指定 device='cpu' 和 trust_remote_code=True
            from sentence_transformers import SentenceTransformer
            import torch
            
            # 强制设置环境变量
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            
            # 直接显式指定 device='cpu' 加载模型
            cls._model = SentenceTransformer(
                RAGConfig.EMBEDDING_MODEL_NAME,
                device='cpu',
                trust_remote_code=True
            )
            
            # 包装 encode 方法，确保返回 numpy 数组
            original_encode = cls._model.encode
            
            def safe_encode(texts, normalize_embeddings=True):
                """
                安全的encode包装函数，确保返回numpy数组格式
                
                Args:
                    texts: 输入文本或文本列表
                    normalize_embeddings: 是否归一化向量
                    
                Returns:
                    numpy.ndarray: 向量化结果
                """
                result = original_encode(
                    texts, 
                    normalize_embeddings=normalize_embeddings,
                    convert_to_numpy=True,
                    convert_to_tensor=False
                )
                return result
            
            cls._model.encode = safe_encode
            print(f"✅ Embedding模型加载成功!")
            
        except Exception as e:
            print(f"❌ Embedding模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            cls._model = None
            raise
        finally:
            cls._model_loading = False

    @classmethod
    def embed_text(cls, text: str) -> np.ndarray:
        """
        单个文本向量化
        
        将输入的单个文本转换为高维向量表示，向量已归一化。
        
        Args:
            text: 输入文本字符串
            
        Returns:
            numpy.ndarray: 文本的向量表示，形状为 (embedding_dim,)
            
        Examples:
            >>> vector = EmbeddingService.embed_text("这是一段测试文本")
            >>> print(vector.shape)
            (768,)
        """
        cls._load_model()
        embedding = cls._model.encode(text, normalize_embeddings=True)
        
        # 确保输出是正确的格式
        if isinstance(embedding, np.ndarray):
            if embedding.ndim > 1:
                return embedding.squeeze()
        return embedding

    @classmethod
    def embed_documents(cls, texts: List[str]) -> List[np.ndarray]:
        """
        批量文本向量化
        
        一次处理多个文本，提高处理效率，向量已归一化。
        
        Args:
            texts: 文本字符串列表
            
        Returns:
            List[numpy.ndarray]: 文本向量列表，每个元素形状为 (embedding_dim,)
            
        Examples:
            >>> vectors = EmbeddingService.embed_documents(["文本1", "文本2", "文本3"])
            >>> print(len(vectors))
            3
        """
        cls._load_model()
        embeddings = cls._model.encode(texts, normalize_embeddings=True)
        
        # 确保输出是正确的格式
        if isinstance(embeddings, np.ndarray):
            if embeddings.ndim == 3:
                # [[[...]]] -> [[...]]
                embeddings = embeddings.squeeze(0)
            return list(embeddings)
        elif isinstance(embeddings, list):
            # 如果是列表，检查每个元素
            result = []
            for emb in embeddings:
                if isinstance(emb, np.ndarray) and emb.ndim > 1:
                    result.append(emb.squeeze())
                else:
                    result.append(emb)
            return result
        return embeddings

    @classmethod
    def unload_model(cls):
        """
        卸载模型（释放内存）
        
        手动卸载已加载的Embedding模型并释放相关内存资源。
        下次调用时会重新加载模型。
        """
        cls._model = None
        import gc
        gc.collect()
        print("♻️  Embedding模型已卸载")

