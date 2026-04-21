# 测试模型定义是否正确
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asr_meeting_service.settings')

# 导入Django
import django
django.setup()

# 导入模型
from asr_api.models import MeetingSegment

# 打印模型信息
print("MeetingSegment模型定义成功！")
print(f"模型字段: {[field.name for field in MeetingSegment._meta.fields]}")
print("测试完成，模型定义正确。")
