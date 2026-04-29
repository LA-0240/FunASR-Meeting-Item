# ==========================================
# Embedding服务 - HuggingFace版本
# ==========================================
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
    """文本向量化服务（使用BGE）"""

    _instance = None
    _model = None
    _model_loading = False  # 防止并发加载

    def __new__(cls):
        """单例模式 - 避免重复加载模型"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _load_model(cls):
        """加载Embedding模型（懒加载）"""
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
        Args:
            text: 输入文本
        Returns:
            向量数组
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
        Args:
            texts: 文本列表
        Returns:
            向量列表
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
        """卸载模型（释放内存）"""
        cls._model = None
        import gc
        gc.collect()
        print("♻️  Embedding模型已卸载")

