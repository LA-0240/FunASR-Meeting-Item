#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.
Django管理命令行工具，用于执行各种管理任务
"""
import os
import sys
from pathlib import Path

# ========== 在任何导入前设置环境变量！（最重要的一步！）==========
BASE_DIR = Path(__file__).resolve().parent
HF_CACHE_DIR = os.path.join(BASE_DIR, "hf_cache")

# 强制离线模式 - 阻止所有网络请求！
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# 设置缓存目录
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = HF_CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = HF_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 设置镜像源（以防万一需要下载）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

def main():
    """
    运行管理任务
    
    设置Django环境并执行命令行管理任务
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_meeting_service.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
