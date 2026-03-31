import numpy as np
import torch
from .models import Voiceprint, voiceprint_model

def extract_voiceprint_feature(audio_path):
    """
    官方标准声纹提取 —— 根据你的真实返回值修复！
    """
    try:
        res = voiceprint_model.generate(
            input=audio_path,
            return_spk_emb=True,
            extract_embedding=True,
        )

        if not res or len(res) == 0:
            return None

        # 🔥 🔥 🔥 修复：你的模型返回 key = spk_embedding
        data = res[0]
        tensor_emb = data["spk_embedding"]  # 这里是关键！

        # 🔥 把 tensor 转成 numpy 数组（CPU版本）
        feature = tensor_emb.detach().cpu().numpy().squeeze()
        print("提取的声纹特征维度：", feature.shape)  # 打印维度，如 (192,)
        
        return np.array(feature, dtype=np.float32)
    
    except Exception as e:
        print(f"提取声纹失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return None


def check_voiceprint_duplicate(new_feature, threshold=0.85):
    max_similarity = 0.0
    duplicate_name = None
    voiceprints = Voiceprint.objects.all()
    for vp in voiceprints:
        exist_feature = Voiceprint.binary_to_feature(vp.feature)
        similarity, is_match = Voiceprint.calculate_similarity(new_feature, exist_feature, threshold)
        if similarity > max_similarity:
            max_similarity = similarity
            if is_match:
                duplicate_name = vp.name
    return duplicate_name is not None, duplicate_name, max_similarity


def match_voiceprint(spk_feature, threshold=0.8):
    """修正：添加日志，返回相似度+特征维度，强制打印所有匹配细节"""
    voiceprints = Voiceprint.objects.all()
    if voiceprints.count() == 0:
        print("❌ 声纹库为空，无法匹配")
        return None
    
    max_sim = 0.0
    matched_name = None
    # 打印输入特征的基础信息
    print(f"🔍 待匹配特征维度：{spk_feature.shape}，归一化前范数：{np.linalg.norm(spk_feature):.4f}")
    
    for vp in voiceprints:
        exist_feature = Voiceprint.binary_to_feature(vp.feature)
        # 1. 打印库中特征维度
        print(f"\n📚 声纹库-{vp.name}：维度{exist_feature.shape}，归一化前范数：{np.linalg.norm(exist_feature):.4f}")
        
        # 2. 维度不匹配时的详细提示
        if spk_feature.shape != exist_feature.shape:
            print(f"⚠️ 特征维度不匹配：输入{spk_feature.shape} vs 库中{exist_feature.shape}（{vp.name}）")
            continue
        
        # 3. 计算相似度并打印（保留4位小数）
        similarity, is_match = Voiceprint.calculate_similarity(spk_feature, exist_feature, threshold)
        print(f"✅ {vp.name} 相似度：{similarity:.4f} | 阈值：{threshold} | 是否匹配：{is_match}")
        
        # 4. 更新最高相似度
        if similarity > max_sim:
            max_sim = similarity
            if is_match:
                matched_name = vp.name
    
    # 最终匹配结果汇总
    print(f"\n📊 匹配汇总：最高相似度={max_sim:.4f} | 匹配名称={matched_name} | 阈值={threshold}")
    # 即使未匹配到，也打印最高相似度（关键！）
    if not matched_name:
        print(f"❌ 无匹配结果：最高相似度{max_sim:.4f} < 阈值{threshold}")
    return matched_name