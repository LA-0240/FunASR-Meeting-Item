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
                max_single_segment_time=30,
                # === 优化：VAD和最小说话片段参数 ===
                vad_kwargs={
                    "min_silence_duration_ms": 300,    # 最小静音时长（毫秒）
                    "speech_pad_ms": 200,              # 语音前后填充（毫秒）
                },
                spk_kwargs={
                    "min_spk_len_s": 1.5,              # 最小说话片段时长（秒），过滤超短噪音
                }
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
                # === 优化：选择 TOP 3 最长片段，提取特征取平均 ===
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

                    # ===================== ffmpeg 切割音频 =====================
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

                    # 提取声纹特征
                    feat = extract_voiceprint_feature(clip_path)
                    if feat is not None:
                        features.append(feat)

                # === 优化：多个特征取平均 ===
                if features:
                    avg_feat = np.mean(features, axis=0)  # 平均特征
                    # 只有登录用户才使用声纹匹配
                    user = request.user if request.user.is_authenticated else None
                    print(f"ASR 用户认证状态: {request.user.is_authenticated}")
                    print(f"ASR 用户: {request.user.username if request.user.is_authenticated else '匿名'}")
                    # 传入会议中的说话人数量用于动态阈值
                    name = match_voiceprint(avg_feat, user=user, speaker_count=len(speaker_segments))
                    print(f"ASR 声纹匹配结果 (基于{len(features)}个片段平均): {name}")
                    speaker_name_map[spk_id] = name if name else f"spk-{spk_id}"
                else:
                    speaker_name_map[spk_id] = f"spk-{spk_id}"

                # 清理临时文件
                for clip_path in clip_paths:
                    if os.path.exists(clip_path):
                        os.remove(clip_path)

            # ===================== 步骤3：后处理平滑优化 =====================
            print(f"[{datetime.now()}] 第三步：说话人平滑后处理")
            matched_speakers = {}
            for spk_id, name in speaker_name_map.items():
                if not name.startswith("spk-"):
                    matched_speakers[spk_id] = name

            # 先构建原始结果列表
            raw_result = []
            for seg in sentence_info:
                spk_id = seg.get("spk") or seg.get("sp") or 0
                name = speaker_name_map.get(spk_id, f"spk-{spk_id}")
                
                raw_result.append({
                    "spk": name,
                    "text": seg.get("text", "").strip(),
                    "start_time": round(seg.get("start", 0) / 1000, 2),
                    "end_time": round(seg.get("end", 0) / 1000, 2),
                    "original_spk": spk_id
                })

            # === 优化1：过滤超短片段（<0.5秒）===
            temp_result = []
            for seg in raw_result:
                duration = seg["end_time"] - seg["start_time"]
                if duration >= 0.5:  # 只保留>=0.5秒的片段
                    temp_result.append(seg)
                else:
                    # 超短片段的文本附到上一个同说话人
                    if temp_result and temp_result[-1]["spk"] == seg["spk"]:
                        temp_result[-1]["text"] += " " + seg["text"]
                        temp_result[-1]["end_time"] = seg["end_time"]

            # === 优化2：合并同一说话人连续片段（间隔<3秒）===
            formatted_result = []
            for seg in temp_result:
                if formatted_result and formatted_result[-1]["spk"] == seg["spk"]:
                    prev = formatted_result[-1]
                    gap = seg["start_time"] - prev["end_time"]
                    if gap < 3.0:  # 间隔小于3秒，合并
                        prev["text"] += " " + seg["text"]
                        prev["end_time"] = seg["end_time"]
                    else:
                        formatted_result.append(seg)
                else:
                    formatted_result.append(seg)

            # ===================== 返回 =====================
            return Response({
                "status": "success",
                "filename": file.name,
                "transcription": formatted_result,
                "sentence_info": sentence_info,  # 新增：返回原始句子数据（不合并）
                "speaker_stats": {
                    "total_speakers": len(speaker_ids),
                    "speaker_ids": sorted(list(speaker_ids)),
                    "matched_speakers": matched_speakers,
                    "total_sentences": len(sentence_info),  # 新增：原始句子总数
                    "merged_sentences": len(formatted_result)  # 新增：合并后句子数
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