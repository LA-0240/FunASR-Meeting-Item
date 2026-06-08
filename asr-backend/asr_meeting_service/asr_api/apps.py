"""
ASR API应用配置模块
配置Django应用的基本信息和初始化
"""
from django.apps import AppConfig


class AsrApiConfig(AppConfig):
    """ASR API应用配置类"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'asr_api'

    def ready(self):
        """应用启动时初始化，加载AI模型
        """
        from .models import ready
        ready()