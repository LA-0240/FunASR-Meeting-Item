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

# ------------------- 视频上传+语音转写 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VideoASRTranscribeView(APIView):
    authentication_classes = [BearerTokenAuthentication, TokenAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        """
        视频上传接口：提取音频→ASR转写→说话人分离→声纹匹配
        返回：带正确说话人名的转写文本
        """
        temp_video = None
        temp_audio = None
        try:
            # 1. 校验文件是否上传
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传视频文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            # 2. 校验视频格式
            if not file.name.lower().endswith(settings.ALLOWED_VIDEO_EXTENSIONS):
                return Response(
                    {"status": "failed", "detail": f"仅支持以下视频格式：{settings.ALLOWED_VIDEO_EXTENSIONS}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 保存临时视频文件
            video_filename = f"temp_video_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}_{file.name}"
            temp_video = os.path.join(settings.TEMP_DIR, video_filename)
            with open(temp_video, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # 4. 提取音频（WAV格式）
            audio_filename = f"temp_audio_{uuid.uuid4()}.wav"
            temp_audio = os.path.join(settings.TEMP_DIR, audio_filename)
            if not extract_audio_from_video(temp_video, temp_audio):
                return Response(
                    {"status": "failed", "detail": "视频音频提取失败"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 5. 解析请求参数
            batch_size_s = request.POST.get("batch_size_s", "")
            try:
                batch_size_s = int(batch_size_s.strip()) if batch_size_s.strip() else 300
            except (ValueError, TypeError):
                batch_size_s = 300
            hotword = request.POST.get("hotword", None)
            
            # 6. 调用ASR模型
            print(f"[{datetime.now()}] 视频处理第一步：说话人分离 + ASR识别")
            try:
                result = asr_model.generate(
                    input=temp_audio,
                    batch_size_s=batch_size_s,
                    hotword=hotword,
                    punc=True,
                    spk_segment=True,
                    speaker_diarization=True,
                    merge_vad=True,
                    max_single_segment_time=30
                )
            except IndexError as e:
                print(f"{datetime.now()} - 说话人识别失败，降级为纯文本转写：{str(e)}")
                result = asr_model.generate(
                    input=temp_audio,
                    batch_size_s=batch_size_s,
                    hotword=hotword,
                    punc=True,
                    spk_segment=False,
                    merge_vad=True,
                    max_single_segment_time=30
                )
            except Exception as e:
                return Response(
                    {"status": "failed", "detail": f"ASR模型处理失败：{str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            sentence_info = result[0].get("sentence_info", []) if result else []
            if not sentence_info:
                return Response({
                    "status": "success",
                    "filename": file.name,
                    "transcription": [{
                        "spk": "未知说话人",
                        "text": "未识别到有效语音内容",
                        "start_time": 0.00,
                        "end_time": 0.00,
                        "original_spk": 0
                    }],
                    "speaker_stats": {"total_speakers":0,"speaker_ids":[],"matched_speakers":{}},
                    "note": "视频处理完成",
                    "timestamp": datetime.now().isoformat()
                })

            # ===================== 收集说话人时间段 =====================
            speaker_segments = defaultdict(list)
            speaker_ids = set()

            for seg in sentence_info:
                spk_id = seg.get("spk") or seg.get("sp") or 0
                start_ms = seg.get("start", 0)
                end_ms = seg.get("end", 0)
                speaker_segments[spk_id].append((start_ms, end_ms))
                speaker_ids.add(spk_id)

            # ===================== 第二步：每人独立声纹匹配（核心） =====================
            print(f"[{datetime.now()}] 视频处理第二步：{len(speaker_segments)} 个说话人进行声纹匹配")
            speaker_name_map = {}

            for spk_id, segments in speaker_segments.items():
                segments.sort(key=lambda x: x[1]-x[0], reverse=True)
                best_start, best_end = segments[0]
                start_sec = best_start / 1000.0
                duration_sec = (best_end - best_start) / 1000.0
                clip_path = os.path.join(settings.TEMP_DIR, f"vid_clip_{spk_id}.wav")

                # ffmpeg 切割（无pydub）
                subprocess.run([
                    "ffmpeg",
                    "-ss", str(start_sec),
                    "-t", str(duration_sec),
                    "-i", temp_audio,
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",
                    clip_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # 声纹识别
                feat = extract_voiceprint_feature(clip_path)
                if feat is not None:
                    # 只有登录用户才使用声纹匹配
                    user = request.user if request.user.is_authenticated else None
                    print(f"视频处理用户认证状态: {request.user.is_authenticated}")
                    print(f"视频处理用户: {request.user.username if request.user.is_authenticated else '匿名'}")
                    # 传入会议中的说话人数量用于动态阈值
                    name = match_voiceprint(feat, user=user, speaker_count=len(speaker_segments))
                    print(f"视频处理声纹匹配结果: {name}")
                    speaker_name_map[spk_id] = name if name else f"spk-{spk_id}"
                else:
                    speaker_name_map[spk_id] = f"spk-{spk_id}"

                if os.path.exists(clip_path):
                    os.remove(clip_path)

            # ===================== 最终结果拼接 =====================
            formatted_result = []
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
                    "start_time": round(seg.get("start", 0)/1000, 2),
                    "end_time": round(seg.get("end", 0)/1000, 2),
                    "original_spk": spk_id
                })

            # ===================== 返回 =====================
            return Response({
                "status": "success",
                "filename": file.name,
                "transcription": formatted_result,
                "sentence_info": sentence_info,  # 新增：返回原始句子数据
                "speaker_stats": {
                    "total_speakers": len(speaker_ids),
                    "speaker_ids": sorted(list(speaker_ids)),
                    "matched_speakers": matched_speakers,
                    "total_sentences": len(sentence_info),  # 新增：原始句子总数
                    "merged_sentences": len(formatted_result)  # 新增：合并后句子数
                },
                "note": "视频已处理：分离+声纹识别完成",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"视频处理失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            for temp_file in [temp_video, temp_audio]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass