"""
语义分段模块 - 基于 Embedding + KMeans 聚类
=============================================

功能说明：
    将会议逐字稿按"议题/主题"分段，而不是简单地按说话人或长度切分。

核心流程：
    逐字稿 → 切分句子 → 时间窗口合并 → 向量化 → KMeans聚类 → 按时间合并同类

与现有代码的关系：
    - 完全兼容现有 optimize_segments_with_llm_batch / store_segments / serialize_segments
    - 只需把 segment_transcription 替换为 semantic_segment_transcription

依赖：
    - asr_api.rag.embedding.EmbeddingService（已存在）
    - scikit-learn（需要安装：pip install scikit-learn）
    - numpy（已有）
"""

import numpy as np
import os
import sys

# 确保能导入同级模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入向量化服务（项目已有）
try:
    from asr_api.rag.embedding import EmbeddingService
    _EMBEDDING_AVAILABLE = True
except Exception as e:
    print(f"[警告] EmbeddingService 导入失败: {e}")
    _EMBEDDING_AVAILABLE = False


# ============================================================
# 核心函数1：切分句子（与现有 meeting.py 逻辑保持一致）
# ============================================================
def split_sentences(text):
    """
    按标点符号将文本切分为句子列表。

    中文/英文标点都会触发切分：。 ！ ？ ； \n . ! ?

    Args:
        text (str): 原始文本

    Returns:
        list[str]: 句子列表
    """
    if not text or not text.strip():
        return []

    sentences = []
    current = ""
    # 句子结束标点
    end_marks = ["。", "！", "？", "；", "\n", ".", "!", "?"]

    for char in text:
        current += char
        if char in end_marks:
            if current.strip():
                sentences.append(current.strip())
            current = ""

    # 添加最后一句（如果没有以标点结尾）
    if current.strip():
        sentences.append(current.strip())

    return sentences


# ============================================================
# 核心函数2：创建时间窗口（相邻句子合并成一个文本块）
# ============================================================
def create_windows(sentences, window_size=3):
    """
    将相邻句子合并成"窗口"（window），便于做语义聚类。

    例如：
        sentences = [s1, s2, s3, s4, s5, s6, s7]
        window_size = 3
        → windows = [
            {text: s1+s2+s3, start_sent_idx: 0, end_sent_idx: 3},
            {text: s4+s5+s6, start_sent_idx: 3, end_sent_idx: 6},
            {text: s7,        start_sent_idx: 6, end_sent_idx: 7},
          ]

    Args:
        sentences (list[str]): 句子列表
        window_size (int): 每个窗口包含的句子数

    Returns:
        list[dict]: [{"text": ..., "start_sent_idx": ..., "end_sent_idx": ...}, ...]
    """
    if not sentences:
        return []

    windows = []
    for i in range(0, len(sentences), window_size):
        window_text = "".join(sentences[i:i + window_size])
        windows.append({
            "text": window_text,
            "start_sent_idx": i,
            "end_sent_idx": min(i + window_size, len(sentences)),
        })

    return windows


# ============================================================
# 核心函数3：KMeans 语义聚类
# ============================================================
def semantic_cluster(windows, auto_cluster=True, n_clusters=None):
    """
    对窗口文本做语义聚类，返回每个窗口的聚类标签。

    实现说明：
        1. 用项目已有的 BGE Embedding 模型把每个窗口转成 768 维向量
        2. 用 scikit-learn 的 KMeans 做聚类
        3. 自动估算聚类数（如果不指定 n_clusters）

    Args:
        windows (list[dict]): 来自 create_windows 的窗口列表
        auto_cluster (bool): 是否自动确定聚类数
        n_clusters (int|None): 手动指定聚类数（优先级高于 auto_cluster）

    Returns:
        list[int]: 每个窗口的 cluster 标签，如 [0, 0, 1, 1, 2, 2, 0, 0]
    """
    if not windows:
        return []

    # 1. 向量化（调用项目已有 EmbeddingService）
    print(f"[语义分段] 开始向量化，共 {len(windows)} 个窗口")
    texts = [w["text"] for w in windows]
    try:
        embeddings_raw = EmbeddingService.embed_documents(texts)
        embeddings = np.array(embeddings_raw)
    except Exception as e:
        print(f"[语义分段] 向量化失败: {e}")
        # 兜底：退化到所有窗口同一个cluster（即不做切分）
        return [0] * len(windows)

    print(f"[语义分段] 向量化完成，向量维度: {embeddings.shape}")

    # 2. 自动确定聚类数（优先用传入的 n_clusters）
    if n_clusters is None or auto_cluster:
        # 经验公式：每 6 个窗口聚成一个主题，但最少 3 个，最多 10 个
        n_clusters = max(3, min(len(windows) // 6, 10))
        print(f"[语义分段] 自动设置聚类数: {n_clusters}")

    # 保护：窗口数不能少于聚类数
    n_clusters = min(n_clusters, len(windows))

    # 3. KMeans 聚类
    try:
        from sklearn.cluster import KMeans
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,      # 多初始化几次，取最优结果
            max_iter=300
        )
        labels = kmeans.fit_predict(embeddings)
        labels = labels.tolist()  # 转成普通 list
        print(f"[语义分段] KMeans 完成，聚类结果: {labels}")
        return labels
    except Exception as e:
        print(f"[语义分段] KMeans 失败，退化为不做聚类: {e}")
        # 兜底：所有窗口属于同一个cluster
        return [0] * len(windows)


# ============================================================
# 核心函数4：按时间顺序合并同类
# ============================================================
def make_segment(windows_in_cluster, total_duration, total_sentences):
    """
    将一组窗口合并成一个 segment。

    产出的格式与现有 segment_transcription 兼容：
        {
            "start_time": float,   # 秒
            "end_time":   float,   # 秒
            "content":    str,
            "cluster_label": int,  # 调试用，可选
        }
    """
    content = "".join([w["text"] for w in windows_in_cluster])

    # ✅ 修复：按句子位置线性估算时间
    # first_sent_idx / last_sent_idx 是句子索引，分母必须是总句子数 total_sentences
    first_sent_idx = windows_in_cluster[0]["start_sent_idx"]
    last_sent_idx = windows_in_cluster[-1]["end_sent_idx"]

    start_time = (first_sent_idx / total_sentences) * total_duration
    end_time = (last_sent_idx / total_sentences) * total_duration

    return {
        "start_time": start_time,
        "end_time": end_time,
        "content": content,
        "cluster_label": windows_in_cluster[0].get("cluster_label", -1),
    }


def merge_by_cluster(windows, labels, total_duration, total_sentences):
    """
    按时间顺序，将相同 cluster 的相邻窗口合并成一个 segment。

    举例：
        windows = [W1, W2, W3, W4, W5, W6]
        labels  = [0,  0,  1,  1,  0,  0]
        → 合并为 3 个 segment：
            [W1+W2(cluster=0), W3+W4(cluster=1), W5+W6(cluster=0)]

    注意：这里允许同一cluster在不同时间段再次出现（符合会议主题切换的实际情况）。

    Args:
        windows: 窗口列表，每个窗口含 start_sent_idx, end_sent_idx
        labels: 每个窗口的聚类标签
        total_duration: 视频总时长（秒）
        total_sentences: 总句子数，用于时间定位 ✅
    """
    if not windows or not labels:
        return []

    # 先给每个窗口贴上cluster标签，方便 make_segment 调试
    for w, label in zip(windows, labels):
        w["cluster_label"] = label

    segments = []
    current_cluster = labels[0]
    current_windows = [windows[0]]

    for i in range(1, len(windows)):
        if labels[i] == current_cluster:
            # 同cluster，继续累积
            current_windows.append(windows[i])
        else:
            # 不同cluster，保存并开始新的
            segments.append(make_segment(
                current_windows, total_duration, total_sentences  # ✅ 传总句子数
            ))
            current_cluster = labels[i]
            current_windows = [windows[i]]

    # 保存最后一个
    if current_windows:
        segments.append(make_segment(
            current_windows, total_duration, total_sentences  # ✅ 传总句子数
        ))

    return segments


# ============================================================
# 主接口：语义分段入口（替换 meeting.py 中的 segment_transcription）
# ============================================================
def semantic_segment_transcription(
    transcription_text,
    total_duration=3600,
    window_size=3,
    n_clusters=None,
):
    """
    语义分段主入口。

    参数与现有 segment_transcription 保持一致，便于直接替换：
        - transcription_text: 逐字稿全文
        - total_duration: 会议总时长（秒），用于估算每个分段起止时间

    额外参数（可选）：
        - window_size: 每个窗口包含的句子数，默认 3
        - n_clusters: 手动指定聚类数，默认自动估算

    返回值格式与 segment_transcription 完全一致，可直接：
        optimized_segments = optimize_segments_with_llm_batch(initial_segments)
    """
    print(f"[语义分段] ========== 开始语义分段 ==========")
    print(f"[语义分段] 总时长: {total_duration}秒, 窗口大小: {window_size}")

    # ---- 步骤1：切分句子
    sentences = split_sentences(transcription_text)
    total_sentences = len(sentences)  # ✅ 保存总句子数，用于时间估算
    print(f"[语义分段] 步骤1：切分为 {total_sentences} 个句子")

    if total_sentences < 5:
        print("[语义分段] 句子太少，直接返回整段")
        return [{
            "start_time": 0,
            "end_time": total_duration,
            "content": transcription_text,
        }]

    # ---- 步骤2：时间窗口合并
    windows = create_windows(sentences, window_size=window_size)
    print(f"[语义分段] 步骤2：合并为 {len(windows)} 个窗口")

    if len(windows) < 3:
        # 窗口太少（内容很短），不做聚类，直接把窗口当分段
        fallback_segments = []
        for w in windows:
            # ✅ 修复：分母用总句子数，不是窗口数
            start = (w["start_sent_idx"] / total_sentences) * total_duration
            end = (w["end_sent_idx"] / total_sentences) * total_duration
            fallback_segments.append({
                "start_time": start,
                "end_time": end,
                "content": w["text"],
            })
        return fallback_segments

    # ---- 步骤3：语义聚类
    labels = semantic_cluster(windows, n_clusters=n_clusters)

    # ---- 步骤4：按时间顺序合并同类
    segments = merge_by_cluster(windows, labels, total_duration, total_sentences)  # ✅ 传总句子数
    print(f"[语义分段] 步骤4：合并为 {len(segments)} 个分段")

    for i, seg in enumerate(segments):
        print(f"[语义分段]   分段 {i+1}: {seg['start_time']:.0f}s-{seg['end_time']:.0f}s "
              f"(cluster={seg['cluster_label']}, 长度={len(seg['content'])}字)")

    return segments
