# 确保导入路径和拼写完全正确
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

import os
import re
from datetime import timedelta
from django.conf import settings
import ffmpeg

def custom_exception_handler(exc, context):
    """自定义异常处理，对齐FastAPI的异常返回格式"""
    response = exception_handler(exc, context)

    # 如果DRF未处理异常，手动封装
    if response is None:
        if isinstance(exc, Exception):
            return Response(
                {"detail": f"服务器内部错误：{str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return None

    # 统一异常返回格式
    if response.status_code == 400:
        response.data = {"status": "failed", "detail": response.data}
    elif response.status_code == 500:
        response.data = {"status": "failed", "detail": response.data.get("detail", "服务器内部错误")}
    
    return response


def extract_audio_from_video(video_path, output_audio_path):
    """
    从视频中提取音频（WAV格式）
    :param video_path: 视频文件路径
    :param output_audio_path: 输出音频路径
    """
    try:
        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, format='wav', acodec='pcm_s16le', ar='16000', ac=1)
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception as e:
        print(f"提取音频失败：{str(e)}")
        return False