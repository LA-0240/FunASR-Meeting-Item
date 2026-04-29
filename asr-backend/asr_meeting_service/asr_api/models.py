# models.py 最终修复版
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
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
            print(f"{datetime.now()} - ✅ ASR模型加载完成")
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

# 用户模型
class User(AbstractUser):
    """用户模型"""
    email = models.EmailField(unique=True, verbose_name="邮箱")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="头像")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

# 原有的 AudioRecord 模型保持不变
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
    name = models.CharField(max_length=100, verbose_name="声纹名称")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户")  # 新增外键关联
    avatar = models.ImageField(upload_to='voiceprint_avatars/', blank=True, null=True, verbose_name="声纹头像")
    feature = models.BinaryField(verbose_name="声纹特征（二进制存储）")
    file_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="声纹文件路径")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "声纹信息"
        verbose_name_plural = "声纹信息"
        unique_together = ('user', 'name')  # 确保每个用户的声纹名称唯一

    def __str__(self):
        return f"{self.user.username}: {self.name}"

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

# 上传文件模型
class UploadedFile(models.Model):
    """上传文件模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户")
    original_name = models.CharField(max_length=255, verbose_name="原始文件名")
    stored_name = models.CharField(max_length=255, verbose_name="存储文件名", unique=True)
    file_path = models.CharField(max_length=500, verbose_name="文件存储路径")
    file_type = models.CharField(max_length=50, verbose_name="文件类型")  # audio/video
    file_size = models.IntegerField(verbose_name="文件大小（字节）")
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")
    status = models.CharField(max_length=20, default="original", verbose_name="文件状态")  # original/processed
    meeting_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="会议类型")

    class Meta:
        verbose_name = "上传文件"
        verbose_name_plural = "上传文件"

    def __str__(self):
        return self.original_name
    
# 转录模型
class Transcription(models.Model):
    """转录模型"""
    file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, verbose_name="关联文件")
    transcription_text = models.TextField(verbose_name="转录文本")
    speaker_info = models.JSONField(blank=True, null=True, verbose_name="说话人信息（已合并优化）")
    raw_sentence_info = models.JSONField(blank=True, null=True, verbose_name="原始句子数据（未合并）")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "转录记录"
        verbose_name_plural = "转录记录"

# Prompt模板模型
class Prompt(models.Model):
    """Prompt模板模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属用户")
    name = models.CharField(max_length=255, verbose_name="模板名称")
    system_prompt = models.TextField(verbose_name="系统提示词")
    user_prompt = models.TextField(verbose_name="用户提示词")
    category = models.CharField(max_length=20, choices=[('default', '默认'), ('custom', '自定义')], default='custom', verbose_name="分类")
    template_type = models.CharField(max_length=20, choices=[('summary', '纪要'), ('abstract', '摘要')], default='summary', verbose_name="模板类型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "Prompt模板"
        verbose_name_plural = "Prompt模板"

    def __str__(self):
        return f"{self.name} ({self.category}, {self.template_type})"

# 会议纪要模型
class MeetingSummary(models.Model):
    """会议纪要模型"""
    file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, verbose_name="关联文件")
    summary_text = models.TextField(verbose_name="纪要文本")
    abstract_text = models.TextField(blank=True, null=True, verbose_name="摘要文本")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_customized = models.BooleanField(default=False, verbose_name="是否自定义修改")

    class Meta:
        verbose_name = "会议纪要"
        verbose_name_plural = "会议纪要"

# 会议分段模型
class MeetingSegment(models.Model):
    """会议分段时间轴核心模型"""
    file = models.ForeignKey(
        UploadedFile,
        on_delete=models.CASCADE,
        related_name="meeting_segments",
        verbose_name="关联会议文件"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="所属用户"
    )
    segment_index = models.IntegerField(verbose_name="段落序号")
    start_time = models.FloatField(verbose_name="开始时间(秒)")
    end_time = models.FloatField(verbose_name="结束时间(秒)")
    title = models.CharField(max_length=100, verbose_name="段落小标题")
    content = models.TextField(verbose_name="段落原文内容")
    summary = models.TextField(verbose_name="段落核心总结")
    is_edited = models.BooleanField(default=False, verbose_name="是否用户手动编辑")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["segment_index"]
        verbose_name = "会议分段"
        verbose_name_plural = "会议分段列表"

    def __str__(self):
        return f"{self.segment_index} - {self.title}"
