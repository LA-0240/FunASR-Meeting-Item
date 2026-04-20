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


def check_voiceprint_duplicate(feature, user=None):
    """
    检查声纹是否重复
    :param feature: 声纹特征
    :param user: 用户对象（可选），如果提供则只检查该用户的声纹
    :return: (是否重复, 重复的声纹名称, 最大相似度)
    """
    try:
        if user:
            # 只检查当前用户的声纹
            voiceprints = Voiceprint.objects.filter(user=user)
        else:
            # 检查所有声纹（兼容旧逻辑）
            voiceprints = Voiceprint.objects.all()
        
        max_similarity = 0
        duplicate_name = None
        
        for vp in voiceprints:
            vp_feature = Voiceprint.binary_to_feature(vp.feature)
            similarity, _ = Voiceprint.calculate_similarity(feature, vp_feature)
            
            if similarity > max_similarity:
                max_similarity = similarity
                duplicate_name = vp.name
        
        # 相似度阈值
        if max_similarity > 0.85:
            return True, duplicate_name, max_similarity
        return False, None, max_similarity
    except Exception as e:
        print(f"声纹重复检查失败: {e}")
        return False, None, 0

def match_voiceprint(feature, user=None):
    """
    匹配声纹
    :param feature: 声纹特征
    :param user: 用户对象（可选），如果提供则只匹配该用户的声纹
    :return: 匹配的声纹名称，未匹配返回None
    """
    try:
        print(f"声纹匹配用户: {user.username if user and user.is_authenticated else 'None'}")
        
        if user and user.is_authenticated:
            # 只匹配当前用户的声纹
            voiceprints = Voiceprint.objects.filter(user=user)
            print(f"找到 {voiceprints.count()} 个声纹")
        else:
            # 未登录用户，不进行声纹匹配
            print("未登录用户，不进行声纹匹配")
            return None
        
        max_similarity = 0
        matched_name = None
        
        for vp in voiceprints:
            vp_feature = Voiceprint.binary_to_feature(vp.feature)
            similarity, _ = Voiceprint.calculate_similarity(feature, vp_feature)
            print(f"声纹 {vp.name} 相似度: {similarity}")
            
            if similarity > max_similarity:
                max_similarity = similarity
                matched_name = vp.name
        
        # 相似度阈值
        print(f"最大相似度: {max_similarity}")
        if max_similarity > 0.85:
            print(f"匹配成功: {matched_name}")
            return matched_name
        print("无匹配声纹")
        return None
    except Exception as e:
        print(f"声纹匹配失败: {e}")
        return None