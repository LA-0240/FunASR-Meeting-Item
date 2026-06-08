"""
ASGI config for asr_meeting_service project.

ASGI (Asynchronous Server Gateway Interface) 配置文件
提供异步Web服务器接口，支持异步处理请求

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# 设置Django配置模块环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_meeting_service.settings")

# 获取ASGI应用实例
application = get_asgi_application()
