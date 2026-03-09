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

def generate_srt_subtitle(transcription, srt_path):
    """
    基于ASR转写结果生成SRT字幕文件
    :param transcription: ASR转写结果（列表，包含spk/text/start_time/end_time）
    :param srt_path: SRT文件输出路径
    """
    def format_time(seconds):
        """将秒数转换为SRT时间格式：00:00:00,000"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    with open(srt_path, 'w', encoding='utf-8') as f:
        index = 1
        for segment in transcription:
            # 过滤空文本
            if not segment.get('text') or segment['text'].strip() == '':
                continue
            # 格式化时间
            start_time = format_time(segment['start_time'])
            end_time = format_time(segment['end_time'])
            # 拼接SRT条目
            speaker = segment.get('spk', '未知说话人')
            text = segment['text'].strip()
            # SRT格式：序号 + 开始时间 --> 结束时间 + 字幕内容
            f.write(f"{index}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{speaker}：{text}\n\n")
            index += 1
    return index > 1  # 验证是否生成有效字幕