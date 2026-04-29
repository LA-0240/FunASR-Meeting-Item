from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import time
import uuid
from datetime import datetime
import traceback
import numpy as np
from ..models import Voiceprint, asr_model
from ..auth_utils import require_auth
from ..voiceprint_utils import extract_voiceprint_feature, check_voiceprint_duplicate, match_voiceprint

# ------------------- 声纹添加 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VoiceprintAddView(APIView):
    """添加声纹（上传音频提取特征，重复则提示）"""
    @method_decorator(require_auth)  # 添加认证装饰器
    def post(self, request):
        try:
            # 1. 校验参数
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传音频文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            voiceprint_name = request.POST.get("name", "").strip()
            if not voiceprint_name:
                return Response(
                    {"status": "failed", "detail": "声纹名称不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # 校验名称是否已存在（针对当前用户）
            if Voiceprint.objects.filter(name=voiceprint_name, user=request.user).exists():
                return Response(
                    {"status": "failed", "detail": f"声纹名称「{voiceprint_name}」已存在"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 2. 校验音频格式
            file = request.FILES['file']
            if not file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                return Response(
                    {"status": "failed", "detail": f"仅支持音频格式：{settings.ALLOWED_EXTENSIONS}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 保存临时音频文件
            temp_filename = f"vp_temp_{uuid.uuid4()}_{file.name}"
            temp_file = os.path.join(settings.TEMP_DIR, temp_filename)
            with open(temp_file, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # 4. 提取声纹特征
            global asr_model
            if asr_model is None:
                from ..models import load_asr_model
                load_asr_model()
            vp_feature = extract_voiceprint_feature(temp_file)
            if vp_feature is None:
                return Response(
                    {"status": "failed", "detail": "声纹特征提取失败"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 5. 检查是否重复
            is_duplicate, dup_name, max_sim = check_voiceprint_duplicate(vp_feature, user=request.user)  # 传入当前用户
            if is_duplicate:
                return Response(
                    {"status": "failed", "detail": f"检测到相似声纹（相似度{max_sim:.2f}），名称：{dup_name}，不予添加"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 6. 保存声纹文件到指定目录
            # 创建用户目录
            user_dir = os.path.join(settings.VOICEPRINT_DIR, f'user_{request.user.id}')
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            
            # 生成唯一的文件名
            timestamp = time.strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(file.name)[1]
            stored_filename = f'voiceprint_{timestamp}_{random_str}{file_extension}'
            stored_path = os.path.join(user_dir, stored_filename)
            
            # 保存文件
            with open(stored_path, 'wb') as f:
                with open(temp_file, 'rb') as temp_f:
                    f.write(temp_f.read())
            
            # 7. 保存声纹到数据库
            voiceprint = Voiceprint(
                name=voiceprint_name,
                user=request.user,  # 关联当前用户
                feature=Voiceprint.feature_to_binary(vp_feature),
                file_path=stored_path
            )
            voiceprint.save()
            
            # 8. 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return Response({
                "status": "success",
                "detail": f"声纹「{voiceprint_name}」添加成功",
                "voiceprint_id": voiceprint.id,
                "created_at": voiceprint.created_at.isoformat()
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"添加声纹失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 声纹列表 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VoiceprintListView(APIView):
    @method_decorator(require_auth)  # 添加认证装饰器
    def get(self, request):
        try:
            # 获取查询参数
            name = request.query_params.get('name', '').strip()
            
            # 只获取当前用户的声纹
            voiceprints = Voiceprint.objects.filter(user=request.user)
            
            # 如果提供了名称参数，进行过滤
            if name:
                voiceprints = voiceprints.filter(name__icontains=name)
            
            # 按创建时间倒序排序
            voiceprints = voiceprints.order_by("-created_at")
            
            vp_list = [{
                "id": vp.id,
                "name": vp.name,
                "file_path": vp.file_path,
                "avatar_url": f"/media/{vp.avatar.name}" if vp.avatar else None,
                "created_at": vp.created_at.isoformat(),
                "updated_at": vp.updated_at.isoformat()
            } for vp in voiceprints]
            return Response({
                "status": "success",
                "count": len(vp_list),
                "voiceprints": vp_list
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取声纹列表失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 声纹修改 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VoiceprintRenameView(APIView):
    @method_decorator(require_auth)  # 添加认证装饰器
    def post(self, request):
        try:
            # 1. 提取参数
            vp_id = request.data.get("id")
            new_name = request.data.get("new_name", "").strip()
            if not vp_id or not new_name:
                return Response(
                    {"status": "failed", "detail": "声纹ID和新名称不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 2. 检查声纹是否存在（针对当前用户）
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, user=request.user)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 3. 检查新名称是否重复（针对当前用户）
            if Voiceprint.objects.filter(name=new_name, user=request.user).exclude(id=vp_id).exists():
                return Response(
                    {"status": "failed", "detail": f"声纹名称「{new_name}」已存在"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. 修改名称
            old_name = voiceprint.name
            voiceprint.name = new_name
            voiceprint.save()
            
            return Response({
                "status": "success",
                "detail": f"声纹名称从「{old_name}」修改为「{new_name}」成功",
                "voiceprint_id": vp_id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"修改声纹名称失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 声纹删除 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VoiceprintDeleteView(APIView):
    @method_decorator(require_auth)  # 添加认证装饰器
    def post(self, request):
        try:
            # 1. 提取参数
            vp_id = request.data.get("id")
            if not vp_id:
                return Response(
                    {"status": "failed", "detail": "声纹ID不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 2. 检查声纹是否存在（针对当前用户）
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, user=request.user)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 3. 删除声纹文件
            if voiceprint.file_path and os.path.exists(voiceprint.file_path):
                try:
                    os.remove(voiceprint.file_path)
                except Exception as e:
                    pass  # 文件删除失败不影响声纹删除
            
            # 4. 删除声纹
            vp_name = voiceprint.name
            voiceprint.delete()
            
            return Response({
                "status": "success",
                "detail": f"声纹「{vp_name}」删除成功",
                "voiceprint_id": vp_id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"删除声纹失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 声纹文件获取 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VoiceprintAudioView(APIView):
    """获取声纹音频文件（用于前端播放）"""
    @method_decorator(require_auth)  # 添加认证装饰器
    def get(self, request, vp_id):
        try:
            # 1. 检查声纹是否存在（针对当前用户）
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, user=request.user)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 2. 检查文件是否存在
            if not voiceprint.file_path or not os.path.exists(voiceprint.file_path):
                return Response(
                    {"status": "failed", "detail": "声纹文件不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 3. 读取文件内容并返回
            from django.http import FileResponse
            import mimetypes
            
            # 确定文件的MIME类型
            mime_type, _ = mimetypes.guess_type(voiceprint.file_path)
            if not mime_type:
                mime_type = 'audio/wav'  # 默认MIME类型
            
            # 直接使用文件路径创建FileResponse
            try:
                response = FileResponse(open(voiceprint.file_path, 'rb'), content_type=mime_type)
                # 设置文件名
                filename = os.path.basename(voiceprint.file_path)
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                return response
            except Exception as e:
                return Response(
                    {"status": "failed", "detail": f"文件读取失败：{str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取声纹文件失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 声纹头像上传 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VoiceprintAvatarUploadView(APIView):
    """声纹头像上传接口"""
    @method_decorator(require_auth)
    def post(self, request, vp_id):
        try:
            # 1. 检查声纹是否存在（针对当前用户）
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, user=request.user)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 2. 校验参数
            if 'avatar' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传图片文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['avatar']
            # 3. 校验图片格式
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                return Response(
                    {"status": "failed", "detail": f"仅支持图片格式：{allowed_extensions}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. 校验文件大小（5MB）
            if file.size > 5 * 1024 * 1024:
                return Response(
                    {"status": "failed", "detail": "图片大小不能超过5MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 5. 删除旧头像（如果有）
            if voiceprint.avatar:
                try:
                    if os.path.exists(voiceprint.avatar.path):
                        os.remove(voiceprint.avatar.path)
                except:
                    pass
            
            # 6. 保存新头像
            # 生成唯一的文件名
            timestamp = time.strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(file.name)[1]
            new_filename = f'vp_avatar_{voiceprint.id}_{timestamp}_{random_str}{file_extension}'
            
            # 保存到 MEDIA_ROOT/voiceprint_avatars/
            import shutil
            avatar_dir = os.path.join(settings.MEDIA_ROOT, 'voiceprint_avatars')
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir)
            
            avatar_path = os.path.join(avatar_dir, new_filename)
            with open(avatar_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # 7. 更新声纹头像字段
            voiceprint.avatar.name = f'voiceprint_avatars/{new_filename}'
            voiceprint.save()
            
            return Response({
                "status": "success",
                "detail": "头像上传成功",
                "avatar_url": f"/media/voiceprint_avatars/{new_filename}"
            })
            
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"头像上传失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 声纹头像删除 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VoiceprintAvatarDeleteView(APIView):
    """声纹头像删除接口"""
    @method_decorator(require_auth)
    def post(self, request, vp_id):
        try:
            # 1. 检查声纹是否存在（针对当前用户）
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, user=request.user)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 2. 检查是否有头像
            if not voiceprint.avatar:
                return Response(
                    {"status": "failed", "detail": "该声纹没有头像"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 删除头像文件
            try:
                if os.path.exists(voiceprint.avatar.path):
                    os.remove(voiceprint.avatar.path)
            except:
                pass
            
            # 4. 清除数据库中的头像字段
            voiceprint.avatar = None
            voiceprint.save()
            
            return Response({
                "status": "success",
                "detail": "头像删除成功"
            })
            
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"头像删除失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )