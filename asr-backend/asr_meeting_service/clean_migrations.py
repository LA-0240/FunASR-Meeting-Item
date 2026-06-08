#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理数据库迁移和修复脚本
用于清理有问题的数据库迁移记录
"""
import os
import sys

# 添加项目路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asr_meeting_service.settings')

import django
django.setup()

from django.db import connection

def clean_migrations():
    """
    清理迁移记录
    删除有问题的0011开头的迁移记录
    """
    print("开始清理数据库迁移记录...")
    
    with connection.cursor() as cursor:
        # 检查是否有0011的记录
        cursor.execute("SELECT id, name FROM django_migrations WHERE app='asr_api' AND name LIKE '0011%'")
        rows = cursor.fetchall()
        if rows:
            print(f"发现需要删除的迁移记录: {rows}")
            cursor.execute("DELETE FROM django_migrations WHERE app='asr_api' AND name LIKE '0011%'")
            print("已删除0011相关的迁移记录")
        
        # 查看当前状态
        cursor.execute("SELECT id, name FROM django_migrations WHERE app='asr_api' ORDER BY id")
        print("当前asr_api的迁移记录:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
    
    print("\n清理完成！现在可以运行: python manage.py migrate")

if __name__ == '__main__':
    clean_migrations()
