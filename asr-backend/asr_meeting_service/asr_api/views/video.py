"""
视频ASR转录视图模块
提供视频文件的语音转录和说话人声纹识别功能
"""
from django.conf import settings
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
from ..models import Voiceprint, Speaker, asr_model
from ..voiceprint_utils import extract_voiceprint_feature, check_voiceprint_duplicate, match_voiceprint, append_voiceprint
import subprocess
from collections import defaultdict


# 自定义认证类，支持 Bearer Token
class BearerTokenAuthentication(TokenAuthentication):
    """自定义认证类：支持 Bearer Token 格式的认证"""
    keyword = 'Bearer'


# ------------------- 视频ASR语音转文字接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VideoASRTranscribeView(APIView):
    """视频ASR转录视图：将视频文件转录为文字，并进行说话人声纹识别"""
    authentication_classes = [BearerTokenAuthentication, TokenAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        """
        视频ASR语音转文字接口，支持多说话人声纹识别
        
        Args:
            request: HTTP请求对象，包含视频文件和参数
            
        Returns:
            Response: 转录结果和说话人信息
        """
        temp_file = None
        temp_audio = None
        try:
            # 1. 校验文件上传
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传视频文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES['file']
            allowed_video_exts = getattr(settings, 'ALLOWED_VIDEO_EXTENSIONS', ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'))
            if not file.name.lower().endswith(allowed_video_exts):
                return Response(
                    {"status": "failed", "detail": f"仅支持格式：{allowed_video_exts}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. 保存临时文件
            temp_filename = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}_{file.name}"
            temp_file = os.path.join(settings.TEMP_DIR, temp_filename)
            with open(temp_file, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            # 3. 从视频中提取音频
            print(f"[{datetime.now()}] 从视频中提取音频...")
            temp_audio = os.path.join(settings.TEMP_DIR, f"{uuid.uuid4()}_audio.wav")
            extract_audio_from_video(temp_file, temp_audio)

            # 4. 解析参数
            batch_size_s = int(request.POST.get("batch_size_s", 300))
            hotword = request.POST.get("hotword", None)

            # ===================== 步骤1：FunASR 说话人分离 + ASR识别 =====================
            print(f"[{datetime.now()}] 第一步：说话人分离 + 语音识别")
            result = asr_model.generate(
                input=temp_audio,
                batch_size_s=batch_size_s,
                hotword=hotword,
                punc=True,
                spk_segment=True,
                speaker_diarization=True
            )

            # 5. 格式化结果
            formatted_result = []
            speaker_ids = set()
            sentence_info = result[0].get("sentence_info", []) if result else []

            if not sentence_info:
                return Response({
                    "status": "success",
                    "filename": file.name,
                    "segments": [{
                        "speaker": "未知说话人",
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
            speaker_info_map = {}  # {spk_id: {"name": "...", "avatar_url": "...", "speaker_obj": Speaker}}

            for spk_id, segments in speaker_segments.items():
                # 优化：选择 TOP 3 最长片段，提取特征取平均
                segments.sort(key=lambda x: x[1] - x[0], reverse=True)
                top_segments = segments[:3]  # 取最长的3个片段
                clip_paths = []
                features = []

                for idx, (best_start, best_end) in enumerate(top_segments):
                    start_sec = best_start / 1000.0
                    end_sec = best_end / 1000.0
                    duration_sec = end_sec - start_sec

                    # 临时切割片段
                    clip_path = os.path.join(settings.TEMP_DIR, f"speaker_clip_{spk_id}_{idx}.wav")
                    clip_paths.append(clip_path)

                    # ffmpeg 切割音频
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

                    # 提取声纹特征
                    feat = extract_voiceprint_feature(clip_path)
                    if feat is not None:
                        features.append(feat)

                # 优化：多个特征取平均
                if features:
                    avg_feat = np.mean(features, axis=0)  # 平均特征
                    # 只有登录用户才使用声纹匹配
                    user = request.user if request.user.is_authenticated else None
                    print(f"ASR 用户认证状态: {request.user.is_authenticated}")
                    print(f"ASR 用户: {request.user.username if request.user.is_authenticated else '匿名'}")
                    # 传入会议中的说话人数量用于动态阈值
                    result, similarity = match_voiceprint(avg_feat, user=user, speaker_count=len(speaker_segments))

                    # 处理匹配结果
                    if isinstance(result, Speaker):
                        # 匹配到了新模型的 Speaker
                        name = result.name
                        avatar_url = f"/media/{result.avatar.name}" if result.avatar else None
                        speaker_info_map[spk_id] = {
                            "name": name,
                            "avatar_url": avatar_url,
                            "speaker_obj": result
                        }
                        # 如果我们有上传的文件，自动追加声纹
                        if len(segments) > 0:
                            best_start, best_end = segments[0]
                            clip_path = os.path.join(settings.TEMP_DIR, f"voiceprint_append_{uuid.uuid4()}.wav")
                            try:
                                subprocess.run([
                                    "ffmpeg",
                                    "-ss", str(best_start / 1000.0),
                                    "-t", str((best_end - best_start) / 1000.0),
                                    "-i", temp_audio,
                                    "-ar", "16000",
                                    "-ac", "1",
                                    "-y",
                                    clip_path
                                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                                # 追加声纹
                                if user.is_authenticated:
                                    upload_file_obj = getattr(request, 'uploaded_file', None)
                                    append_voiceprint(
                                        speaker=result,
                                        feature=avg_feat,
                                        user=user,
                                        audio_path=clip_path,
                                        source_meeting=upload_file_obj,
                                        source_type='auto'
                                    )
                            finally:
                                if os.path.exists(clip_path):
                                    try:
                                        os.remove(clip_path)
                                    except:
                                        pass
                    else:
                        # 旧模型或者无匹配
                        name = result
                        final_name = name if name else f"spk-{spk_id}"
                        speaker_info_map[spk_id] = {
                            "name": final_name,
                            "avatar_url": None,
                            "speaker_obj": None
                        }

                    print(f"ASR 声纹匹配结果（基于{len(features)}个片段平均）: {name}")
                else:
                    speaker_info_map[spk_id] = {
                        "name": f"spk-{spk_id}",
                        "avatar_url": None,
                        "speaker_obj": None
                    }

                # 清理临时文件
                for clip_path in clip_paths:
                    if os.path.exists(clip_path):
                        os.remove(clip_path)

            # ===================== 步骤3：构建统一格式的分段数据 =====================
            print(f"[{datetime.now()}] 第三步：构建分段数据")
            matched_speakers = {}
            for spk_id, info in speaker_info_map.items():
                name = info["name"]
                if not name.startswith("spk-"):
                    matched_speakers[spk_id] = {
                        "name": name,
                        "avatar_url": info["avatar_url"]
                    }

            # 构建统一格式的结果
            segments = []
            for seg in sentence_info:
                spk_id = seg.get("spk") or seg.get("sp") or 0
                info = speaker_info_map.get(spk_id, {"name": f"spk-{spk_id}", "avatar_url": None})
                name = info["name"]
                avatar_url = info["avatar_url"]

                segments.append({
                    "speaker": name,
                    "avatar_url": avatar_url,
                    "text": seg.get("text", "").strip(),
                    "start_time": round(seg.get("start", 0) / 1000, 2),
                    "end_time": round(seg.get("end", 0) / 1000, 2),
                    "original_spk": spk_id
                })

            # ===================== 返回 =====================
            return Response({
                "status": "success",
                "filename": file.name,
                "segments": segments,
                "speaker_stats": {
                    "total_speakers": len(speaker_ids),
                    "speaker_ids": sorted(list(speaker_ids)),
                    "matched_speakers": matched_speakers,
                    "total_sentences": len(segments)
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
            if temp_audio and os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except:
                    pass
