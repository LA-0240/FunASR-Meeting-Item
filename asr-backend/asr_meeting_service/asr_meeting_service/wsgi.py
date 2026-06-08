"""
WSGI config for asr_meeting_service project.

WSGI (Web Server Gateway Interface) 配置文件
提供Web服务器网关接口，用于连接Web服务器和Django应用

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# 设置Django配置模块环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_meeting_service.settings")

# 获取WSGI应用实例
application = get_wsgi_application()
