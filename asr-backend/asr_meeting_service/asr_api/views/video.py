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
from ..models import Voiceprint, asr_model, Speaker
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
                    speaker_diarization=True
                )
            except IndexError as e:
                print(f"{datetime.now()} - 说话人识别失败，降级为纯文本转写：{str(e)}")
                result = asr_model.generate(
                    input=temp_audio,
                    batch_size_s=batch_size_s,
                    hotword=hotword,
                    punc=True,
                    spk_segment=False
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
            speaker_info_map = {}  # {spk_id: {"name": "...", "avatar_url": "...", "speaker_obj": Speaker}}

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
                    match_result = match_voiceprint(feat, user=user, speaker_count=len(speaker_segments))
                    # 解包返回值 (name, similarity)
                    if isinstance(match_result, tuple) and len(match_result) == 2:
                        speaker_obj, similarity = match_result
                    else:
                        speaker_obj = match_result
                        similarity = 0
                    
                    # 处理匹配结果
                    if isinstance(speaker_obj, Speaker):
                        # 匹配到了新模型的 Speaker
                        name = speaker_obj.name
                        avatar_url = f"/media/{speaker_obj.avatar.name}" if speaker_obj.avatar else None
                        speaker_info_map[spk_id] = {
                            "name": name,
                            "avatar_url": avatar_url,
                            "speaker_obj": speaker_obj
                        }
                    else:
                        # 旧模型或者无匹配
                        name = speaker_obj
                        final_name = name if name else f"spk-{spk_id}"
                        speaker_info_map[spk_id] = {
                            "name": final_name,
                            "avatar_url": None,
                            "speaker_obj": None
                        }
                    
                    print(f"视频处理声纹匹配结果: name={name}, similarity={similarity}")
                else:
                    speaker_info_map[spk_id] = {
                        "name": f"spk-{spk_id}",
                        "avatar_url": None,
                        "speaker_obj": None
                    }

                if os.path.exists(clip_path):
                    os.remove(clip_path)

            # ===================== 最终结果拼接 =====================
            matched_speakers = {}
            for spk_id, info in speaker_info_map.items():
                name = info["name"]
                if name and isinstance(name, str) and not name.startswith("spk-"):
                    matched_speakers[spk_id] = {
                        "name": name,
                        "avatar_url": info["avatar_url"]
                    }

            segments = []
            for seg in sentence_info:
                spk_id = seg.get("spk") or seg.get("sp") or 0
                info = speaker_info_map.get(spk_id, {"name": f"spk-{spk_id}", "avatar_url": None})
                name = info["name"]
                avatar_url = info["avatar_url"]
                # 确保 name 是 string
                if not name or not isinstance(name, str):
                    name = f"spk-{spk_id}"
                segments.append({
                    "speaker": name,
                    "avatar_url": avatar_url,
                    "text": seg.get("text", "").strip(),
                    "start_time": round(seg.get("start", 0)/1000, 2),
                    "end_time": round(seg.get("end", 0)/1000, 2),
                    "original_spk": spk_id
                })

            # ===================== 返回 =====================
            return Response({
                "status": "success",
                "filename": file.name,
                "transcription": segments,
                "sentence_info": segments,  # 兼容旧接口
                "segments": segments,  # 新接口字段
                "speaker_stats": {
                    "total_speakers": len(speaker_ids),
                    "speaker_ids": sorted(list(speaker_ids)),
                    "matched_speakers": matched_speakers,
                    "total_sentences": len(segments)
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