from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from ..models import UploadedFile, Transcription, Voiceprint, Speaker
from ..auth_utils import require_auth
from .asr import ASRTranscribeView
from .video import VideoASRTranscribeView
import traceback
import re
import os

# ------------------- 逐字稿搜索接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class TranscriptionSearchView(APIView):
    @method_decorator(require_auth)
    def post(self, request):
        """逐字稿搜索接口"""
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            keyword = request.data.get("keyword", "").strip()

            # 清理关键词，去除无效字符
            keyword = keyword.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            
            # 2. 输入校验
            if not file_id:
                return Response(
                    {"status": "failed", "detail": "文件ID不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            if not keyword:
                return Response(
                    {"status": "failed", "detail": "搜索关键词不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 3. 检查文件是否存在且属于当前用户
            try:
                file = UploadedFile.objects.get(id=file_id, user=request.user)
            except UploadedFile.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "文件不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 4. 检查逐字稿是否存在
            try:
                transcription = Transcription.objects.get(file=file)
            except Transcription.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "逐字稿不存在"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 5. 解析逐字稿数据（兼容新旧字段）
            segments = transcription.segments or []
            if not segments:
                return Response(
                    {"status": "failed", "detail": "逐字稿内容为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 6. 搜索关键词（支持大小写不敏感）
            matches = []
            keyword_lower = keyword.lower()
            for index, sentence in enumerate(segments):
                text = sentence.get("text", "")
                if keyword_lower in text.lower():
                    # 生成高亮文本（大小写不敏感）
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    highlighted_text = pattern.sub(
                        r"<span class='highlight-yellow'>\g<0></span>",
                        text
                    )
                    
                    matches.append({
                        "id": index + 1,
                        "speaker": sentence.get("speaker", ""),
                        "text": text,
                        "highlighted_text": highlighted_text,
                        "start_time": sentence.get("start_time", 0),
                        "end_time": sentence.get("end_time", 0),
                        "sentence_index": index
                    })
            
            # 7. 返回搜索结果
            return Response({
                "status": "success",
                "file_id": file_id,
                "keyword": keyword,
                "total_matches": len(matches),
                "matches": matches
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"搜索失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 获取逐字稿接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class TranscriptionGetView(APIView):
    @method_decorator(require_auth)
    def get(self, request, file_id):
        """获取指定文件的逐字稿"""
        try:
            # 1. 检查文件是否存在且属于当前用户
            try:
                file = UploadedFile.objects.get(id=file_id, user=request.user)
            except UploadedFile.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "文件不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 2. 检查逐字稿是否存在
            try:
                transcription = Transcription.objects.get(file=file)
            except Transcription.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "逐字稿不存在"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 3. 获取统一的分段数据
            segments = transcription.segments or []
            # 获取当前用户的所有 Speaker
            speakers = {sp.name: sp for sp in Speaker.objects.filter(user=request.user)}
            
            # 为每条记录添加 avatar_url
            segments_with_avatar = []
            for item in segments:
                speaker_name = item.get('speaker', '') or item.get('spk', '')
                # 尝试匹配 Speaker 头像
                avatar_url = None
                if speaker_name in speakers:
                    sp = speakers[speaker_name]
                    if sp.avatar:
                        avatar_url = f"/media/{sp.avatar.name}"
                segments_with_avatar.append({
                    **item,
                    'avatar_url': avatar_url
                })
            
            # 4. 准备返回数据
            return Response({
                "status": "success",
                "file_id": file_id,
                "file_name": file.original_name,
                "transcription_text": transcription.transcription_text,
                "segments": segments_with_avatar,
                "created_at": transcription.created_at.isoformat(),
                "updated_at": transcription.updated_at.isoformat()
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取逐字稿失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 编辑逐字稿接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class TranscriptionEditView(APIView):
    @method_decorator(require_auth)
    def put(self, request):
        """编辑逐字稿指定句子"""
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            sentence_index = request.data.get("sentence_index")
            text = request.data.get("text", "").strip()
            speaker = request.data.get("speaker")
            
            # 2. 输入校验
            if not file_id or sentence_index is None:
                return Response(
                    {"status": "failed", "detail": "文件ID和句子索引不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 3. 检查文件是否存在且属于当前用户
            try:
                file = UploadedFile.objects.get(id=file_id, user=request.user)
            except UploadedFile.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "文件不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 4. 检查逐字稿是否存在
            try:
                transcription = Transcription.objects.get(file=file)
            except Transcription.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "逐字稿不存在"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 5. 解析逐字稿数据（兼容新旧字段）
            segments = transcription.segments or []
            if not segments:
                return Response(
                    {"status": "failed", "detail": "逐字稿内容为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 6. 验证句子索引
            if sentence_index < 0 or sentence_index >= len(segments):
                return Response(
                    {"status": "failed", "detail": "句子索引无效"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 7. 修改句子
            original_sentence = segments[sentence_index].copy()
            
            # 修改文本（只修改当前句子）
            if text:
                segments[sentence_index]["text"] = text
            
            # 修改说话人（批量修改所有相同说话人的句子）
            if speaker:
                original_speaker = original_sentence.get("speaker", "")
                if original_speaker:
                    updated_count = 0
                    for i, item in enumerate(segments):
                        if item.get("speaker") == original_speaker:
                            segments[i]["speaker"] = speaker
                            updated_count += 1
                    # 记录更新数量
                    batch_updated = updated_count
                else:
                    # 如果原始说话人为空，只更新当前句子
                    segments[sentence_index]["speaker"] = speaker
                    batch_updated = 1
            else:
                batch_updated = 0
            
            # 8. 重新生成转录文本
            transcription_text = '\n'.join([f"{item.get('speaker', '未知说话人')}: {item.get('text', '')}" for item in segments])
            
            # 9. 保存修改
            transcription.segments = segments
            transcription.transcription_text = transcription_text
            transcription.save()
            
            # 10. 返回结果
            response_data = {
                "status": "success",
                "file_id": file_id,
                "sentence_index": sentence_index,
                "original_sentence": original_sentence,
                "updated_sentence": segments[sentence_index],
                "segments": segments
            }
            
            # 如果修改了说话人，返回批量更新信息
            if speaker:
                response_data["original_speaker"] = original_sentence.get("speaker", "")
                response_data["new_speaker"] = speaker
                response_data["batch_updated"] = batch_updated
            
            return Response(response_data, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"编辑失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 生成逐字稿接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class TranscriptionGenerateView(APIView):
    @method_decorator(require_auth)
    def post(self, request):
        """为指定文件生成逐字稿"""
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            force_regenerate = request.data.get("force_regenerate", False)
            
            # 2. 输入校验
            if not file_id:
                return Response(
                    {"status": "failed", "detail": "文件ID不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 3. 检查文件是否存在且属于当前用户
            try:
                file = UploadedFile.objects.get(id=file_id, user=request.user)
            except UploadedFile.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "文件不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 4. 检查逐字稿是否已存在
            try:
                existing_transcription = Transcription.objects.get(file=file)
                if not force_regenerate:
                    return Response(
                        {"status": "failed", "detail": "逐字稿已存在"},
                        status=HTTP_400_BAD_REQUEST
                    )
            except Transcription.DoesNotExist:
                pass
            
            # 5. 检查文件是否存在于磁盘
            if not os.path.exists(file.file_path):
                return Response(
                    {"status": "failed", "detail": "文件不存在于磁盘"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 6. 根据文件类型调用对应的ASR接口
            if file.file_type == "audio":
                # 调用音频ASR
                asr_view = ASRTranscribeView()
                # 模拟请求对象
                from django.http import HttpRequest
                from django.core.files.uploadedfile import InMemoryUploadedFile
                import io
                
                # 读取文件内容
                with open(file.file_path, 'rb') as f:
                    file_content = f.read()
                
                # 创建InMemoryUploadedFile
                file_name = file.stored_name  # 使用存储的文件名，确保扩展名正确
                file_size = file.file_size
                file_extension = os.path.splitext(file_name)[1]
                
                # 确定文件类型
                if file_extension.lower() in ['.wav', '.mp3', '.flac', '.ogg']:
                    content_type = f'audio/{file_extension[1:]}'
                else:
                    content_type = 'audio/*'
                
                mock_file = InMemoryUploadedFile(
                    io.BytesIO(file_content),
                    None,
                    file_name,
                    content_type,
                    file_size,
                    None
                )
                
                # 创建模拟请求
                mock_request = HttpRequest()
                mock_request.FILES = {'file': mock_file}
                mock_request.POST = {
                    'batch_size_s': '300',
                    'hotword': ''
                }
                mock_request.user = request.user
                mock_request.META = request.META
                
                # 调用ASR接口
                asr_response = asr_view.post(mock_request)
                
            else:
                # 调用视频ASR
                video_view = VideoASRTranscribeView()
                # 模拟请求对象
                from django.http import HttpRequest
                from django.core.files.uploadedfile import InMemoryUploadedFile
                import io
                
                # 读取文件内容
                with open(file.file_path, 'rb') as f:
                    file_content = f.read()
                
                # 创建InMemoryUploadedFile
                file_name = file.stored_name  # 使用存储的文件名，确保扩展名正确
                file_size = file.file_size
                file_extension = os.path.splitext(file_name)[1]
                
                # 确定文件类型
                if file_extension.lower() in ['.mp4', '.avi', '.mov', '.wmv']:
                    content_type = f'video/{file_extension[1:]}'
                else:
                    content_type = 'video/*'
                
                mock_file = InMemoryUploadedFile(
                    io.BytesIO(file_content),
                    None,
                    file_name,                    content_type,
                    file_size,
                    None
                )
                
                # 创建模拟请求
                mock_request = HttpRequest()
                mock_request.FILES = {'file': mock_file}
                mock_request.POST = {
                    'batch_size_s': '300',
                    'hotword': ''
                }
                mock_request.user = request.user
                mock_request.META = request.META
                
                # 调用视频ASR接口
                asr_response = video_view.post(mock_request)
            
            # 7. 处理ASR响应
            if asr_response.status_code != HTTP_200_OK:
                return Response(
                    {"status": "failed", "detail": f"ASR处理失败：{asr_response.data.get('detail', '未知错误')}"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 8. 提取转录结果（使用新的segments字段）
            transcription_data = asr_response.data
            segments = transcription_data.get('segments', transcription_data.get('transcription', []))
            
            # 9. 格式化统一的segments
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
            
            # 10. 生成转录文本
            transcription_text = '\n'.join([f"{item['speaker']}: {item['text']}" for item in unified_segments])
            
            # 11. 保存或更新逐字稿
            try:
                # 如果已存在，更新
                transcription = Transcription.objects.get(file=file)
                transcription.transcription_text = transcription_text
                transcription.segments = unified_segments
                transcription.save()
            except Transcription.DoesNotExist:
                # 如果不存在，创建新的
                transcription = Transcription(
                    file=file,
                    transcription_text=transcription_text,
                    segments=unified_segments
                )
                transcription.save()
            
            # 12. 更新文件状态
            file.status = "processed"
            file.save()
            
            # 13. 返回结果
            return Response({
                "status": "success",
                "detail": "逐字稿生成成功",
                "file_id": file.id,
                "file_name": file.original_name,
                "file_type": file.file_type,
                "transcription_id": transcription.id,
                "segments": unified_segments,
                "speaker_stats": transcription_data.get('speaker_stats', {})
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"生成逐字稿失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

