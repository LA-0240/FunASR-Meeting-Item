from django.conf import settings
# from django.http import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
import os
import time
import uuid
from datetime import datetime
import traceback
import numpy as np
from ..utils import extract_audio_from_video
from ..models import Voiceprint, asr_model
from ..voiceprint_utils import extract_voiceprint_feature, check_voiceprint_duplicate, match_voiceprint
import subprocess
from collections import defaultdict

# 自定义认证类，支持 Bearer Token
class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'

# ------------------- ASR语音转文字接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class ASRTranscribeView(APIView):
    authentication_classes = [BearerTokenAuthentication, TokenAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        """语音转文字接口，支持多说话人声纹识别（两步法：分离→切割→匹配）"""
        temp_file = None
        try:
            # 1. 校验文件上传
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传音频文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES['file']
            if not file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                return Response(
                    {"status": "failed", "detail": f"仅支持格式：{settings.ALLOWED_EXTENSIONS}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. 保存临时文件
            temp_filename = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}_{file.name}"
            temp_file = os.path.join(settings.TEMP_DIR, temp_filename)
            with open(temp_file, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            # 3. 解析参数
            batch_size_s = int(request.POST.get("batch_size_s", 300))
            hotword = request.POST.get("hotword", None)

            # ===================== 步骤1：FunASR 说话人分离 + ASR识别 =====================
            print(f"[{datetime.now()}] 第一步：说话人分离 + 语音识别")
            result = asr_model.generate(
                input=temp_file,
                batch_size_s=batch_size_s,
                hotword=hotword,
                punc=True,
                spk_segment=True,
                speaker_diarization=True,
                merge_vad=True,
                max_single_segment_time=30
            )

            # 4. 格式化结果
            formatted_result = []
            speaker_ids = set()
            sentence_info = result[0].get("sentence_info", []) if result else []

            if not sentence_info:
                return Response({
                    "status": "success",
                    "filename": file.name,
                    "transcription": [{
                        "spk": "未知说话人",
                        "text": "未识别到有效内容",
                        "start_time": 0.00,
                        "end_time": 0.00,
                        "original_spk": "unknown"
                    }],
                    "speaker_stats": {"total_speakers": 0, "speaker_ids": [], "matched_speakers": {}},
                    "note": "已启用标点恢复+说话人识别+时间戳",
                    "timestamp": datetime.now().isoformat()
                })

            # ===================== 收集所有说话人的时间段 =====================
            speaker_segments = defaultdict(list)
            for seg in sentence_info:
                spk_id = seg.get("spk") or seg.get("sp") or 0
                start_ms = seg.get("start", 0)
                end_ms = seg.get("end", 0)
                speaker_segments[spk_id].append((start_ms, end_ms))
                speaker_ids.add(spk_id)

            # ===================== 步骤2：对每个说话人，用ffmpeg切割 → 声纹匹配 =====================
            print(f"[{datetime.now()}] 第二步：说话人声纹匹配（共{len(speaker_segments)}人）")
            speaker_name_map = {}

            for spk_id, segments in speaker_segments.items():
                # 选择最长的一段语音来识别（最准确）
                segments.sort(key=lambda x: x[1] - x[0], reverse=True)
                best_start, best_end = segments[0]

                start_sec = best_start / 1000.0
                end_sec = best_end / 1000.0
                duration_sec = end_sec - start_sec

                # 临时切割片段
                clip_path = os.path.join(settings.TEMP_DIR, f"speaker_clip_{spk_id}.wav")

                # ===================== ffmpeg 切割音频（核心！不需要pydub） =====================
                subprocess.run([
                    "ffmpeg",
                    "-ss", str(start_sec),
                    "-t", str(duration_sec),
                    "-i", temp_file,
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",
                    clip_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # 提取声纹 + 匹配
                feat = extract_voiceprint_feature(clip_path)
                if feat is not None:
                    # 只有登录用户才使用声纹匹配
                    user = request.user if request.user.is_authenticated else None
                    print(f"ASR 用户认证状态: {request.user.is_authenticated}")
                    print(f"ASR 用户: {request.user.username if request.user.is_authenticated else '匿名'}")
                    name = match_voiceprint(feat, user=user)  # 传入当前用户（如果已登录）
                    print(f"ASR 声纹匹配结果: {name}")
                    speaker_name_map[spk_id] = name if name else f"spk-{spk_id}"
                else:
                    speaker_name_map[spk_id] = f"spk-{spk_id}"

                # 删除临时片段
                if os.path.exists(clip_path):
                    os.remove(clip_path)

            # ===================== 最终结果替换名字 =====================
            matched_speakers = {}
            for spk_id, name in speaker_name_map.items():
                if not name.startswith("spk-"):
                    matched_speakers[spk_id] = name

            for seg in sentence_info:
                spk_id = seg.get("spk") or seg.get("sp") or 0
                name = speaker_name_map.get(spk_id, f"spk-{spk_id}")

                formatted_result.append({
                    "spk": name,
                    "text": seg.get("text", "").strip(),
                    "start_time": round(seg.get("start", 0) / 1000, 2),
                    "end_time": round(seg.get("end", 0) / 1000, 2),
                    "original_spk": spk_id
                })

            # ===================== 返回 =====================
            return Response({
                "status": "success",
                "filename": file.name,
                "transcription": formatted_result,
                "speaker_stats": {
                    "total_speakers": len(speaker_ids),
                    "speaker_ids": sorted(list(speaker_ids)),
                    "matched_speakers": matched_speakers
                },
                "note": "已启用标点恢复+说话人识别+时间戳 + 离线声纹匹配",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"处理失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass