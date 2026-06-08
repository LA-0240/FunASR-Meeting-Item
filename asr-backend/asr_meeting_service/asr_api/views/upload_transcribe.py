"""
文件上传与自动转录视图模块
提供文件上传并自动进行ASR转录的功能
"""
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from ..models import UploadedFile, Transcription, asr_model
from ..auth_utils import require_auth
from .asr import ASRTranscribeView
from .video import VideoASRTranscribeView
import os
import uuid
from datetime import datetime
import traceback
import json

# 文件存储目录
FILE_STORAGE_DIR = os.path.join(settings.BASE_DIR, 'uploaded_files')
if not os.path.exists(FILE_STORAGE_DIR):
    os.makedirs(FILE_STORAGE_DIR)

# ------------------- 文件上传自动转录接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class FileUploadTranscribeView(APIView):
    """文件上传与自动转录视图：上传音频或视频文件后自动进行ASR转录"""
    @method_decorator(require_auth)
    def post(self, request):
        """
        文件上传自动转录接口：上传文件后自动进行ASR转录并存储逐字稿
        
        Args:
            request: HTTP请求对象，包含文件和会议类型
            
        Returns:
            Response: 包含转录结果的响应
        """
        try:
            # 1. 校验文件上传
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传文件"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            meeting_type = request.POST.get("meeting_type", "").strip()
            
            # 2. 确定文件类型
            if file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                file_type = "audio"
            elif file.name.lower().endswith(settings.ALLOWED_VIDEO_EXTENSIONS):
                file_type = "video"
            else:
                return Response(
                    {"status": "failed", "detail": "不支持的文件格式"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 3. 保存文件
            file_extension = os.path.splitext(file.name)[1]
            stored_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(FILE_STORAGE_DIR, stored_name)
            
            with open(file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # 4. 创建文件记录
            uploaded_file = UploadedFile(
                user=request.user,
                original_name=file.name,
                stored_name=stored_name,
                file_path=file_path,
                file_type=file_type,
                file_size=file.size,
                meeting_type=meeting_type,
                status="processing"
            )
            uploaded_file.save()
            
            # 5. 根据文件类型调用对应的ASR接口
            if file_type == "audio":
                # 调用音频ASR
                asr_view = ASRTranscribeView()
                # 模拟请求对象
                from django.http import HttpRequest
                from django.core.files.uploadedfile import InMemoryUploadedFile
                
                # 创建模拟请求
                mock_request = HttpRequest()
                mock_request.FILES = {'file': file}
                mock_request.POST = {
                    'batch_size_s': '300',
                    'hotword': ''
                }
                mock_request.user = request.user
                mock_request.META = request.META
                mock_request.uploaded_file = uploaded_file  # 🔧 把 uploaded_file 放到 mock_request 上！
                
                # 调用ASR接口
                asr_response = asr_view.post(mock_request)
                
            else:
                # 调用视频ASR
                video_view = VideoASRTranscribeView()
                # 模拟请求对象
                from django.http import HttpRequest
                from django.core.files.uploadedfile import InMemoryUploadedFile
                
                # 创建模拟请求
                mock_request = HttpRequest()
                mock_request.FILES = {'file': file}
                mock_request.POST = {
                    'batch_size_s': '300',
                    'hotword': ''
                }
                mock_request.user = request.user
                mock_request.META = request.META
                mock_request.uploaded_file = uploaded_file  # 🔧 把 uploaded_file 放到 mock_request 上！
                
                # 调用视频ASR接口
                asr_response = video_view.post(mock_request)
            
            # 6. 处理ASR响应
            if asr_response.status_code != HTTP_200_OK:
                # ASR处理失败，更新文件状态
                uploaded_file.status = "failed"
                uploaded_file.save()
                return Response(
                    {"status": "failed", "detail": f"ASR处理失败：{asr_response.data.get('detail', '未知错误')}"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 7. 提取转录结果（使用新的 segments 字段）
            transcription_data = asr_response.data
            segments = transcription_data.get('segments', transcription_data.get('transcription', []))
            
            # 8. 格式化统一的 segments
            unified_segments = []
            for item in segments:
                # 兼容两种格式：spk 或 speaker
                speaker_name = item.get('spk', item.get('speaker', '未知说话人'))
                unified_segments.append({
                    'speaker': speaker_name,
                    'avatar_url': item.get('avatar_url'),
                    'text': item.get('text', ''),
                    'start_time': item.get('start_time', 0),
                    'end_time': item.get('end_time', 0),
                    'original_spk': item.get('original_spk', '')
                })
            
            # 9. 生成转录文本
            transcription_text = '\n'.join([f"{item['speaker']}: {item['text']}" for item in unified_segments])
            
            # 10. 保存逐字稿
            transcription = Transcription(
                file=uploaded_file,
                transcription_text=transcription_text,
                segments=unified_segments
            )
            transcription.save()
            
            # 11. 更新文件状态
            uploaded_file.status = "processed"
            uploaded_file.save()
            
            # 12. 返回结果
            return Response({
                "status": "success",
                "detail": "文件上传并转录成功",
                "file_id": uploaded_file.id,
                "original_name": uploaded_file.original_name,
                "file_type": uploaded_file.file_type,
                "file_size": uploaded_file.file_size,
                "upload_time": uploaded_file.upload_time.isoformat(),
                "meeting_type": uploaded_file.meeting_type,
                "transcription_id": transcription.id,
                "segments": unified_segments,
                "speaker_stats": transcription_data.get('speaker_stats', {})
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"处理失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )
