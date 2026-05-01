import numpy as np
import torch
import os
from django.conf import settings
from .models import Voiceprint, Speaker, voiceprint_model

MAX_VOICEPRINTS_PER_SPEAKER = 4

def extract_voiceprint_feature(audio_path, use_vad=False, vad_mode='strict'):
    """
    官方标准声纹提取
    
    :param audio_path: 音频文件路径
    :param use_vad: 是否启用 VAD 清洗（已禁用）
    :param vad_mode: VAD 模式 ('strict'/'normal'/'loose')
    """
    cleaned_path = None
    try:
        # === VAD 数据清洗 ===
        if use_vad:
            print(f"[声纹提取] ⚠️ VAD 已禁用，直接使用原音频")
        
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
    finally:
        # 清理 VAD 清洗后的临时文件
        if cleaned_path and cleaned_path != audio_path and os.path.exists(cleaned_path):
            try:
                os.remove(cleaned_path)
                print(f"[声纹提取] 🗑️ 已清理 VAD 临时文件: {cleaned_path}")
            except:
                pass


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
        
        voiceprint_count = voiceprints.count()
        max_similarity = 0
        duplicate_name = None
        
        for vp in voiceprints:
            vp_feature = Voiceprint.binary_to_feature(vp.feature)
            similarity, _ = Voiceprint.calculate_similarity(feature, vp_feature)
            
            if similarity > max_similarity:
                max_similarity = similarity
                duplicate_name = vp.name
        
        # 根据声纹数量动态调整阈值
        if voiceprint_count >= 10:
            threshold = 0.75
            print(f"声纹重复检查：声纹数量 {voiceprint_count} 较多，使用较低阈值: {threshold}")
        else:
            threshold = 0.85
            print(f"声纹重复检查：声纹数量 {voiceprint_count} 较少，使用标准阈值: {threshold}")
        
        # 相似度阈值判断
        if max_similarity > threshold:
            return True, duplicate_name, max_similarity
        return False, None, max_similarity
    except Exception as e:
        print(f"声纹重复检查失败: {e}")
        return False, None, 0

def match_voiceprint(feature, user=None, speaker_count=None):
    """
    匹配声纹（支持一人多声纹）
    :param feature: 声纹特征
    :param user: 用户对象（可选），如果提供则只匹配该用户的声纹
    :param speaker_count: 会议文件中的说话人数量（可选），用于动态调整阈值
    :return: (匹配的 Speaker 对象, 最高相似度)，未匹配返回 (None, 0)
    """
    try:
        print(f"声纹匹配用户: {user.username if user and user.is_authenticated else 'None'}")
        
        if not (user and user.is_authenticated):
            print("未登录用户，不进行声纹匹配")
            return None, 0
        
        # 优先匹配新的 Speaker 模型（一人多声纹）
        speakers = Speaker.objects.filter(user=user)
        print(f"找到 {speakers.count()} 个说话人")
        
        max_similarity = 0
        matched_speaker = None
        
        # 对每个 Speaker，检查其所有 Voiceprint，取最高相似度
        for speaker in speakers:
            speaker_max_sim = 0
            voiceprints = speaker.voiceprints.all()
            
            for vp in voiceprints:
                vp_feature = Voiceprint.binary_to_feature(vp.feature)
                similarity, _ = Voiceprint.calculate_similarity(feature, vp_feature)
                print(f"说话人 {speaker.name} 的声纹相似度: {similarity}")
                
                if similarity > speaker_max_sim:
                    speaker_max_sim = similarity
            
            if speaker_max_sim > max_similarity:
                max_similarity = speaker_max_sim
                matched_speaker = speaker
        
        # 如果没有匹配到新模型，尝试兼容旧模型（单个 Voiceprint 无 Speaker）
        if not matched_speaker:
            print("尝试兼容旧模型（单个声纹）")
            old_voiceprints = Voiceprint.objects.filter(user=user, speaker__isnull=True)
            
            for vp in old_voiceprints:
                vp_feature = Voiceprint.binary_to_feature(vp.feature)
                similarity, _ = Voiceprint.calculate_similarity(feature, vp_feature)
                print(f"旧声纹 {vp.name} 相似度: {similarity}")
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    matched_speaker = None
                    matched_name = vp.name
        
        # 根据会议文件中的说话人数量动态调整阈值
        if speaker_count is not None and speaker_count >= 10:
            threshold = 0.75
            print(f"会议说话人数量 {speaker_count} 较多，使用较低阈值: {threshold}")
        else:
            threshold = 0.85
            if speaker_count is not None:
                print(f"会议说话人数量 {speaker_count} 较少，使用标准阈值: {threshold}")
            else:
                print(f"未指定会议说话人数量，使用标准阈值: {threshold}")
        
        print(f"最大相似度: {max_similarity}")
        if max_similarity > threshold:
            if matched_speaker:
                print(f"匹配成功（新模型）: {matched_speaker.name}")
                return matched_speaker, max_similarity
            else:
                print(f"匹配成功（旧模型）: {matched_name}")
                return matched_name, max_similarity
        
        print("无匹配声纹")
        return None, 0
    except Exception as e:
        print(f"声纹匹配失败: {e}")
        import traceback
        traceback.print_exc()
        return None, 0


def append_voiceprint(speaker, feature, user=None, audio_file=None, audio_path=None, source_meeting=None, source_type='auto'):
    """
    给说话人追加一条新声纹
    :param speaker: Speaker 对象
    :param feature: 声纹特征向量
    :param user: 用户对象（可选）
    :param audio_file: 绑定的音频文件（可选，Django File 对象）
    :param audio_path: 音频文件路径（可选，本地文件路径）
    :param source_meeting: 来源会议（UploadedFile 对象，可选）
    :param source_type: 声纹来源类型（'auto' 或 'manual'，默认 'auto'）
    :return: 创建的 Voiceprint 对象，或者如果相似度超过96%则返回 None（不添加）
    """
    try:
        # 如果是 auto 声纹，先检查是否有已有的 auto 声纹
        if source_type == 'auto':
            auto_voiceprints = speaker.voiceprints.filter(source_type='auto')
            if auto_voiceprints.exists():
                # 有 auto 声纹，检查相似度
                max_similarity = 0
                for vp in auto_voiceprints:
                    vp_feature = Voiceprint.binary_to_feature(vp.feature)
                    similarity, _ = Voiceprint.calculate_similarity(feature, vp_feature)
                    print(f"说话人 {speaker.name} 已有的 auto 声纹相似度: {similarity:.4f}")
                    if similarity > max_similarity:
                        max_similarity = similarity
                
                # 如果相似度超过 96%，不添加
                if max_similarity >= 0.96:
                    print(f"声纹相似度 {max_similarity:.4f} >= 0.96，不添加重复声纹")
                    return None
                
                print(f"最高相似度 {max_similarity:.4f} < 0.96，继续添加声纹")
        
        existing_count = speaker.voiceprints.count()
        print(f"说话人 {speaker.name} 当前声纹数: {existing_count}")
        
        # 如果声纹数量已达上限，永远保留最早的那条 manual，删其他的
        if existing_count >= MAX_VOICEPRINTS_PER_SPEAKER:
            voiceprints = speaker.voiceprints.order_by('created_at')
            
            # 1. 找到最早的那条 manual（永远保留！）
            oldest_manual_vp = voiceprints.filter(source_type='manual').first()
            vp_to_delete = None
            
            # 2. 从剩下的里面找要删的
            remaining_vps = voiceprints.exclude(id=oldest_manual_vp.id) if oldest_manual_vp else voiceprints
            
            # 优先删最早的 auto
            auto_vps = remaining_vps.filter(source_type='auto')
            if auto_vps.exists():
                vp_to_delete = auto_vps.first()
                print(f"删除最早的自动追加声纹: {vp_to_delete}")
            else:
                # 如果没有 auto，删后来追加的 manual（但最早的那条永远保留）
                other_manual_vps = remaining_vps.filter(source_type='manual')
                if other_manual_vps.exists():
                    vp_to_delete = other_manual_vps.first()
                    print(f"删除后来追加的手动声纹: {vp_to_delete}")
                else:
                    print(f"只剩最开始的那条声纹了，不删除")
            
            if vp_to_delete:
                # 删除关联的音频文件
                if vp_to_delete.audio_file:
                    try:
                        if os.path.exists(vp_to_delete.audio_file.path):
                            os.remove(vp_to_delete.audio_file.path)
                            print(f"已删除音频文件: {vp_to_delete.audio_file.path}")
                    except:
                        pass
                
                if vp_to_delete.file_path:
                    try:
                        if os.path.exists(vp_to_delete.file_path):
                            os.remove(vp_to_delete.file_path)
                            print(f"已删除旧版音频文件: {vp_to_delete.file_path}")
                    except:
                        pass
                
                vp_to_delete.delete()
        
        # 创建新声纹
        voiceprint = Voiceprint.objects.create(
            speaker=speaker,
            user=user if user else speaker.user,
            feature=Voiceprint.feature_to_binary(feature),
            source_type=source_type,  # 使用传入的 source_type
            source_meeting=source_meeting
        )
        
        # 🔧 修复：正确保存音频文件到 media/voiceprint_audio 目录下！
        if audio_path and os.path.exists(audio_path):
            # 有本地音频文件路径 → 通过 Django FileField 保存
            from django.core.files import File
            import uuid
            from datetime import datetime
            
            # 生成唯一的文件名
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4())[:8]
            new_filename = f"voiceprint_{timestamp}_{random_str}.wav"
            
            # 打开文件并保存
            with open(audio_path, 'rb') as f:
                django_file = File(f, name=new_filename)
                voiceprint.audio_file.save(new_filename, django_file, save=True)
            print(f"append_voiceprint: 已从本地路径 {audio_path} 保存音频到 {voiceprint.audio_file.path}")
        
        elif audio_file:
            # 直接有 Django File 对象 → 直接保存
            voiceprint.audio_file = audio_file
            voiceprint.save()
            print(f"append_voiceprint: 已直接保存音频文件 {audio_file.name}")
        
        print(f"追加声纹成功: {voiceprint}")
        return voiceprint
    except Exception as e:
        print(f"追加声纹失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# 保持向后兼容的旧函数名
def match_voiceprint_old(feature, user=None, speaker_count=None):
    """
    旧版声纹匹配（向后兼容）
    :return: 匹配的名称（字符串）或 None
    """
    result, _ = match_voiceprint(feature, user, speaker_count)
    if isinstance(result, Speaker):
        return result.name
    return result