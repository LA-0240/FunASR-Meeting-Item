from django.conf import settings  # 修正拼写错误
from django.db import models
from datetime import datetime
import os

# 先注释模型加载，确保Django能正常启动，后续再测试ASR功能
asr_model = None

def load_asr_model():
    """加载ASR模型（先注释，确保项目能启动）"""
    global asr_model
    if asr_model is None:
        print(f"{datetime.now()} - 开始加载ASR模型（CPU模式）...")
        try:
            # 先注释funasr导入，确保migrate能执行，后续安装成功后取消注释
            from funasr import AutoModel
            asr_model = AutoModel(
                model="paraformer-zh",
                vad_model="fsmn-vad",
                punc_model="ct-punc",
                spk_model="cam++",
                device="cpu"
            )
            print(f"{datetime.now()} - ASR模型加载完成（测试模式）")
        except Exception as e:
            print(f"{datetime.now()} - ASR模型加载失败: {str(e)}")
            raise

# Django启动时加载模型
def ready():
    import os
    if os.environ.get('RUN_MAIN'):  # 避免Django自动重载时重复加载
        load_asr_model()

class AudioRecord(models.Model):
    """音频文件记录"""
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