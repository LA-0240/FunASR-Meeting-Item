"""
文件管理视图模块
提供文件上传、列表、重命名、下载、删除等功能
"""
from django.conf import settings
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from ..models import UploadedFile, Transcription, MeetingSummary
from ..auth_utils import require_auth
import os
import uuid
from datetime import datetime
import traceback

# 文件存储目录
FILE_STORAGE_DIR = os.path.join(settings.BASE_DIR, 'uploaded_files')
if not os.path.exists(FILE_STORAGE_DIR):
    os.makedirs(FILE_STORAGE_DIR)

# ------------------- 文件上传接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class FileUploadView(APIView):
    """
    文件上传视图
    支持上传音频和视频文件
    """
    @method_decorator(require_auth)
    def post(self, request):
        """
        文件上传
        
        Args:
            request: HTTP请求对象，包含文件和会议类型
            
        Returns:
            Response: 包含上传结果的响应
        """
        try:
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传文件"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            meeting_type = request.POST.get("meeting_type", "").strip()
            
            # 确定文件类型
            if file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                file_type = "audio"
            elif file.name.lower().endswith(settings.ALLOWED_VIDEO_EXTENSIONS):
                file_type = "video"
            else:
                return Response(
                    {"status": "failed", "detail": "不支持的文件格式"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 生成唯一文件名
            file_extension = os.path.splitext(file.name)[1]
            stored_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(FILE_STORAGE_DIR, stored_name)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # 创建文件记录
            uploaded_file = UploadedFile(
                user=request.user,
                original_name=file.name,
                stored_name=stored_name,
                file_path=file_path,
                file_type=file_type,
                file_size=file.size,
                meeting_type=meeting_type
            )
            uploaded_file.save()
            
            return Response({
                "status": "success",
                "detail": "文件上传成功",
                "file_id": uploaded_file.id,
                "original_name": uploaded_file.original_name,
                "stored_name": uploaded_file.stored_name,
                "file_type": uploaded_file.file_type,
                "file_size": uploaded_file.file_size,
                "upload_time": uploaded_file.upload_time.isoformat()
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"文件上传失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 文件列表接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class FileListView(APIView):
    """
    文件列表视图
    获取用户的文件列表，支持搜索功能
    """
    @method_decorator(require_auth)
    def get(self, request):
        """
        获取用户文件列表，支持按文件名、类型和会议类型搜索
        
        Args:
            request: HTTP请求对象，包含搜索参数
            
        Returns:
            Response: 包含文件列表的响应
        """
        try:
            # 获取搜索参数
            search_name = request.query_params.get("name", "").strip()
            search_type = request.query_params.get("type", "").strip()
            search_meeting_type = request.query_params.get("meeting_type", "").strip()
            
            # 构建查询
            query = UploadedFile.objects.filter(user=request.user)
            
            # 按文件名模糊搜索
            if search_name:
                query = query.filter(original_name__icontains=search_name)
            
            # 按文件类型搜索
            if search_type:
                query = query.filter(file_type=search_type)
            
            # 按会议类型模糊搜索
            if search_meeting_type:
                query = query.filter(meeting_type__icontains=search_meeting_type)
            
            # 按上传时间倒序排序
            files = query.order_by("-upload_time")
            
            file_list = []
            for file in files:
                file_info = {
                    "file_id": file.id,
                    "original_name": file.original_name,
                    "stored_name": file.stored_name,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "upload_time": file.upload_time.isoformat(),
                    "status": file.status,
                    "meeting_type": file.meeting_type
                }
                
                # 检查是否有转录和纪要
                try:
                    transcription = Transcription.objects.get(file=file)
                    file_info["has_transcription"] = True
                except Transcription.DoesNotExist:
                    file_info["has_transcription"] = False
                
                try:
                    summary = MeetingSummary.objects.get(file=file)
                    file_info["has_summary"] = True
                    file_info["is_customized"] = summary.is_customized
                except MeetingSummary.DoesNotExist:
                    file_info["has_summary"] = False
                
                file_list.append(file_info)
            
            return Response({
                "status": "success",
                "count": len(file_list),
                "files": file_list,
                "search_params": {
                    "name": search_name,
                    "type": search_type,
                    "meeting_type": search_meeting_type
                }
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取文件列表失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 文件重命名接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class FileRenameView(APIView):
    """
    文件重命名视图
    支持修改文件名和会议类型
    """
    @method_decorator(require_auth)
    def post(self, request):
        """
        文件重命名，支持修改会议类型
        
        Args:
            request: HTTP请求对象，包含文件ID、新名称和会议类型
            
        Returns:
            Response: 包含重命名结果的响应
        """
        try:
            file_id = request.data.get("file_id")
            new_name = request.data.get("new_name", "").strip()
            meeting_type = request.data.get("meeting_type", None)
            
            if not file_id or not new_name:
                return Response(
                    {"status": "failed", "detail": "文件ID和新名称不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 查找文件
            try:
                file = UploadedFile.objects.get(id=file_id, user=request.user)
            except UploadedFile.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "文件不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 更新文件名
            file.original_name = new_name
            
            # 如果提供了会议类型参数，则更新
            if meeting_type is not None:
                file.meeting_type = meeting_type.strip()
            
            file.save()
            
            return Response({
                "status": "success",
                "detail": "文件重命名成功",
                "file_id": file.id,
                "new_name": file.original_name,
                "meeting_type": file.meeting_type
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"文件重命名失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 文件下载接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class FileDownloadView(APIView):
    """
    文件下载视图
    支持HTTP Range请求，播放器直接访问时不需要认证
    """
    def get(self, request, file_id):
        """
        下载文件，支持HTTP Range请求，播放器直接访问时不需要认证
        
        Args:
            request: HTTP请求对象
            file_id: 文件ID
            
        Returns:
            FileResponse/StreamingHttpResponse: 文件响应
        """
        try:
            # 查找文件，不限制用户（播放器无法携带token）
            try:
                file = UploadedFile.objects.get(id=file_id)
            except UploadedFile.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "文件不存在"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 检查文件是否存在
            if not os.path.exists(file.file_path):
                return Response(
                    {"status": "failed", "detail": "文件已被删除"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 获取文件信息
            path = file.file_path
            size = os.path.getsize(path)
            content_type = self.get_content_type(file.original_name)
            
            # 处理 Range 请求
            range_header = request.META.get('HTTP_RANGE', None)
            if range_header:
                return self.handle_range_request(path, size, content_type, file.original_name, range_header)
            else:
                # 没有 Range 请求，返回完整文件
                response = FileResponse(open(path, 'rb'))
                response['Content-Type'] = content_type
                response['Content-Length'] = str(size)
                response['Accept-Ranges'] = 'bytes'
                response['Content-Disposition'] = f'inline; filename="{file.original_name}"'
                return response
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"文件下载失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )
    
    def handle_range_request(self, path, file_size, content_type, filename, range_header):
        """
        处理 Range 请求
        
        Args:
            path: 文件路径
            file_size: 文件大小
            content_type: 内容类型
            filename: 文件名
            range_header: Range请求头
            
        Returns:
            StreamingHttpResponse: 流式响应
        """
        from django.http import StreamingHttpResponse
        
        # 解析 Range 头
        byte_start, byte_end = self.parse_range(range_header, file_size)
        
        # 创建文件流式响应
        def file_stream():
            with open(path, 'rb') as f:
                f.seek(byte_start)
                remaining = byte_end - byte_start + 1
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        # 创建响应
        response = StreamingHttpResponse(file_stream(), status=206)
        response['Content-Type'] = content_type
        response['Content-Length'] = str(byte_end - byte_start + 1)
        response['Content-Range'] = f'bytes {byte_start}-{byte_end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    
    def parse_range(self, range_header, file_size):
        """
        解析 Range 头
        
        Args:
            range_header: Range请求头
            file_size: 文件大小
            
        Returns:
            tuple: (start, end) 字节范围
        """
        # 默认范围
        start = 0
        end = file_size - 1
        
        try:
            # 解析: bytes=start-end
            if not range_header.startswith('bytes='):
                return start, end
            
            range_value = range_header[6:]  # 去掉 'bytes='
            if '-' not in range_value:
                return start, end
            
            range_parts = range_value.split('-', 1)
            
            # 处理 start-
            if range_parts[0]:
                start = int(range_parts[0])
            
            # 处理 -end
            if len(range_parts) > 1 and range_parts[1]:
                end = int(range_parts[1])
            
            # 确保范围有效
            start = max(0, start)
            end = min(file_size - 1, end)
            
            if start > end:
                start = 0
                end = file_size - 1
        
        except (ValueError, IndexError):
            start = 0
            end = file_size - 1
        
        return start, end
    
    def get_content_type(self, filename):
        """
        根据文件名获取 Content-Type
        
        Args:
            filename: 文件名
            
        Returns:
            str: Content-Type
        """
        ext = filename.lower().split('.')[-1]
        
        # 音频类型
        audio_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac',
            'm4a': 'audio/mp4',
            'aac': 'audio/aac',
            'wma': 'audio/x-ms-wma'
        }
        
        # 视频类型
        video_types = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'ogg': 'video/ogg',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime',
            'mkv': 'video/x-matroska',
            'flv': 'video/x-flv',
            'wmv': 'video/x-ms-wmv'
        }
        
        if ext in audio_types:
            return audio_types[ext]
        elif ext in video_types:
            return video_types[ext]
        else:
            return 'application/octet-stream'

# ------------------- 文件删除接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class FileDeleteView(APIView):
    """
    文件删除视图
    删除文件及其关联的转录和纪要数据
    """
    @method_decorator(require_auth)
    def post(self, request):
        """
        文件删除
        
        Args:
            request: HTTP请求对象，包含文件ID
            
        Returns:
            Response: 包含删除结果的响应
        """
        try:
            file_id = request.data.get("file_id")
            
            if not file_id:
                return Response(
                    {"status": "failed", "detail": "文件ID不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 查找文件
            try:
                file = UploadedFile.objects.get(id=file_id, user=request.user)
            except UploadedFile.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "文件不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 删除相关数据
            try:
                transcription = Transcription.objects.get(file=file)
                transcription.delete()
            except Transcription.DoesNotExist:
                pass
            
            try:
                summary = MeetingSummary.objects.get(file=file)
                summary.delete()
            except MeetingSummary.DoesNotExist:
                pass
            
            # 删除物理文件
            if os.path.exists(file.file_path):
                os.remove(file.file_path)
            
            # 删除文件记录
            file_name = file.original_name
            file.delete()
            
            return Response({
                "status": "success",
                "detail": f"文件「{file_name}」删除成功"
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"文件删除失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )