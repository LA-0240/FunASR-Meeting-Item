#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线模式测试脚本 - 确保在导入模型前设置好所有环境变量"""

import os
import sys
from pathlib import Path

# ========== 第1步：立即设置所有环境变量（在任何导入之前！）==========
BASE_DIR = Path(__file__).resolve().parent
HF_CACHE_DIR = os.path.join(BASE_DIR, "hf_cache")

# 强制离线模式
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# 设置缓存目录
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = HF_CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = HF_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 设置镜像源（以防需要）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

print("=" * 60)
print("Forced offline mode - no network requests allowed!")
print(f"HuggingFace cache directory: {HF_CACHE_DIR}")
print("=" * 60)

# ========== 第2步：设置Django环境 ==========
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_meeting_service.settings")
import django
django.setup()
print("\nDjango environment loaded!")

# ========== 第3步：测试导入和模型加载 ==========
print("\n" + "=" * 60)
print("Testing RAG module import...")
print("=" * 60)

from asr_api.rag import EmbeddingService, Retriever

print("\nRAG module imported successfully!")

# ========== 第4步：测试Embedding模型 ==========
print("\n" + "=" * 60)
print("Testing Embedding model loading...")
print("=" * 60)

# 先预加载模型
EmbeddingService._load_model()

# 测试简单的embedding
test_text = "这是一个测试文本"
embedding = EmbeddingService.embed_text(test_text)
print(f"Embedding test passed! Vector dimension: {len(embedding)}")

# ========== 第5步：测试检索（如果向量库有数据）==========
print("\n" + "=" * 60)
print("Testing retrieval...")
print("=" * 60)

# 测试检索
query = "这次会议的主要决定是什么？"
results = Retriever.search(query, file_id=3)

if results:
    print(f"Retrieval successful! Found {len(results)} results")
    for i, r in enumerate(results[:2], 1):
        print(f"\n{i}. Score: {r.get('rerank_score', r.get('similarity')):.3f}")
        print(f"   {r['document'][:80]}...")
else:
    print("No relevant content found (may need to index file first)")

print("\n" + "=" * 60)
print("All offline tests passed!")
print("=" * 60)
