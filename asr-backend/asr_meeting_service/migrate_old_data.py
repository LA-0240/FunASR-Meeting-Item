"""
旧数据迁移脚本
将旧字段 speaker_info / raw_sentence_info 的数据迁移到新字段 segments
"""
import os
import django

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_meeting_service.settings")
django.setup()

from asr_api.models import Transcription

print("🔄 [开始数据迁移] 将 speaker_info / raw_sentence_info 迁移到 segments...")

# 获取所有转录记录
transcriptions = Transcription.objects.all()
count = 0

for transcription in transcriptions:
    # 如果 segments 为空，从旧字段迁移
    if not transcription.segments:
        old_data = transcription.speaker_info or transcription.raw_sentence_info
        if old_data:
            transcription.segments = old_data
            transcription.save()
            count += 1
            print(f"✅ [迁移成功] ID={transcription.id}, 文件={transcription.file.original_name}")

print(f"\n📊 [统计] 共迁移 {count} 条记录")
print("✅ [数据迁移完成]")
