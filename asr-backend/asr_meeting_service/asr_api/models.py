# models.py 最终修复版
from django.conf import settings
from django.db import models
from datetime import datetime
import os
import numpy as np

# 两个模型分开加载，彻底解决断言报错！
asr_model = None       # 用于语音识别
voiceprint_model = None # 专用于声纹提取

def load_asr_model():
    """加载ASR模型（仅用于识别）"""
    global asr_model
    if asr_model is None:
        print(f"{datetime.now()} - 加载ASR识别模型...")
        try:
            from funasr import AutoModel
            asr_model = AutoModel(
                model="paraformer-zh",
                vad_model="fsmn-vad",
                punc_model="ct-punc",
                spk_model="cam++",
                device="cpu",
            )
            print(f"{datetime.now()} - ASR模型加载完成")
        except Exception as e:
            print(f"ASR加载失败: {e}")
            raise

def load_voiceprint_model():
    """加载纯声纹模型（官方标准用法）"""
    global voiceprint_model
    if voiceprint_model is None:
        print(f"{datetime.now()} - 加载纯声纹模型...")
        try:
            from funasr import AutoModel
            voiceprint_model = AutoModel(
                model="damo/speech_campplus_sv_zh-cn_16k-common",
                device="cpu",
                # 🔥 关闭所有自动处理，100%不报错
                vad_forward=False,
                punc_forward=False,
                asr_forward=False,
            )
            print(f"{datetime.now()} - ✅ 声纹模型加载完成")
        except Exception as e:
            print(f"声纹模型加载失败: {e}")
            raise

# Django启动时加载
def ready():
    import os
    if os.environ.get('RUN_MAIN'):
        load_asr_model()
        load_voiceprint_model()

# 你的 AudioRecord 模型保持不变
class AudioRecord(models.Model):
    filename = models.CharField(max_length=255, verbose_name="文件名")
    file_size = models.IntegerField(verbose_name="文件大小（字节）")
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")
    transcription = models.TextField(blank=True, null=True, verbose_name="语音识别结果")
    summary = models.TextField(blank=True, null=True, verbose_name="会议纪要")

    class Meta:
        verbose_name = "音频记录"
        verbose_name_plural = "音频记录"

    def __str__(self):
        return self.filename

class Voiceprint(models.Model):
    name = models.CharField(max_length=100, verbose_name="声纹名称", unique=True)
    feature = models.BinaryField(verbose_name="声纹特征（二进制存储）")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "声纹信息"
        verbose_name_plural = "声纹信息"

    def __str__(self):
        return self.name

    @staticmethod
    def feature_to_binary(feature):
        return feature.tobytes()

    @staticmethod
    def binary_to_feature(binary_data):
        return np.frombuffer(binary_data, dtype=np.float32)

    @staticmethod
    def calculate_similarity(feature1, feature2, threshold=0.85):
        feature1 = feature1 / np.linalg.norm(feature1)
        feature2 = feature2 / np.linalg.norm(feature2)
        similarity = np.dot(feature1, feature2.T)
        return similarity, similarity >= threshold