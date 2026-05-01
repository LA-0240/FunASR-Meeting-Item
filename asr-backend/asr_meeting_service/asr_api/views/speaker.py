from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import uuid
from datetime import datetime
import traceback
import numpy as np
from ..models import Speaker, Voiceprint
from ..auth_utils import require_auth
from ..voiceprint_utils import extract_voiceprint_feature, append_voiceprint, check_voiceprint_duplicate, match_voiceprint

# ------------------- Speaker 列表 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerListView(APIView):
    @method_decorator(require_auth)
    def get(self, request):
        try:
            name = request.query_params.get('name', '').strip()
            
            speakers = Speaker.objects.filter(user=request.user)
            
            if name:
                speakers = speakers.filter(name__icontains=name)
            
            speakers = speakers.order_by("-created_at")
            
            sp_list = []
            for sp in speakers:
                voiceprints = sp.voiceprints.order_by("-created_at")
                vp_list = []
                for vp in voiceprints:
                    # 🔧 双重支持：优先用 media 目录，否则用旧接口
                    audio_url = None
                    print(f'[DEBUG] Speaker {sp.name} 声纹 {vp.id}:')
                    print(f'  - audio_file 是否存在? {bool(vp.audio_file)}')
                    if vp.audio_file:
                        print(f'  - audio_file.name: {vp.audio_file.name}')
                        # 把所有 \ 替换成 /
                        safe_path = vp.audio_file.name.replace('\\', '/')
                        audio_url = f"/media/{safe_path}"
                    else:
                        # 用旧的 /voiceprint/audio/ 接口
                        print(f'  - 无 audio_file，用旧接口')
                        audio_url = f"/voiceprint/audio/{vp.id}"
                    print(f'  - 最终 audio_url: {audio_url}')
                    
                    vp_list.append({
                        "id": vp.id,
                        "speaker_id": sp.id,
                        "audio_url": audio_url,
                        "source_type": vp.source_type,
                        "source_meeting_id": vp.source_meeting_id if vp.source_meeting else None,
                        "created_at": vp.created_at.isoformat()
                    })
                
                sp_list.append({
                    "id": sp.id,
                    "name": sp.name,
                    "avatar_url": f"/media/{sp.avatar.name}" if sp.avatar else None,
                    "voiceprints_count": voiceprints.count(),
                    "voiceprints": vp_list,
                    "created_at": sp.created_at.isoformat(),
                    "updated_at": sp.updated_at.isoformat()
                })
            
            print(f'[DEBUG] 最终返回的 Speaker 列表: {sp_list}')
            
            return Response({
                "status": "success",
                "count": len(sp_list),
                "speakers": sp_list
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取说话人列表失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Speaker 创建 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerAddView(APIView):
    """创建 Speaker，可选择同时上传第一条声纹，会预匹配库里是否有相似人"""
    @method_decorator(require_auth)
    def post(self, request):
        try:
            speaker_name = request.POST.get("name", "").strip()
            if not speaker_name:
                return Response(
                    {"status": "failed", "detail": "说话人名称不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if Speaker.objects.filter(name=speaker_name, user=request.user).exists():
                return Response(
                    {"status": "failed", "detail": f"说话人「{speaker_name}」已存在"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 🔧 新增：预匹配检查
            matched_speaker = None
            max_similarity = 0
            vp_feature = None
            temp_file = None
            file = None
            
            if 'file' in request.FILES:
                file = request.FILES['file']
                if not file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                    return Response(
                        {"status": "failed", "detail": f"仅支持音频格式：{settings.ALLOWED_EXTENSIONS}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                temp_filename = f"vp_temp_{uuid.uuid4()}_{file.name}"
                temp_file = os.path.join(settings.TEMP_DIR, temp_filename)
                with open(temp_file, "wb") as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                
                vp_feature = extract_voiceprint_feature(temp_file)
                
                if vp_feature is None:
                    if temp_file and os.path.exists(temp_file):
                        os.remove(temp_file)
                    return Response(
                        {"status": "failed", "detail": "声纹特征提取失败"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # 预匹配
                result, similarity = match_voiceprint(vp_feature, user=request.user, speaker_count=0)
                if result is not None:
                    matched_speaker = result
                    max_similarity = similarity
            
            # 检查是否强制创建
            force_create = request.POST.get("force_create", "").lower() == "true"
            
            # 如果匹配到了，且没有强制创建，返回 warning
            if matched_speaker is not None and not force_create:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                
                # 判断是 Speaker 对象还是旧声纹字符串
                if isinstance(matched_speaker, str):
                    # 旧声纹（字符串）
                    return Response({
                        "status": "warning",
                        "detail": f"检测到和库里的声纹「{matched_speaker}」很相似！（相似度: {max_similarity:.2f}）",
                        "similar_speaker": {
                            "name": matched_speaker
                        }
                    }, status=200)
                else:
                    # Speaker 对象
                    return Response({
                        "status": "warning",
                        "detail": f"检测到和库里的「{matched_speaker.name}」很相似！（相似度: {max_similarity:.2f}）",
                        "similar_speaker": {
                            "id": matched_speaker.id,
                            "name": matched_speaker.name,
                            "avatar_url": f"/media/{matched_speaker.avatar.name}" if matched_speaker.avatar else None
                        }
                    }, status=200)
            
            # 创建 Speaker
            speaker = Speaker.objects.create(
                name=speaker_name,
                user=request.user
            )
            
            # 如果上传了文件，添加声纹
            if vp_feature is not None and temp_file is not None and file is not None:
                # 保存到 media/voiceprint_audio/ 目录（Django会自动托管）
                import shutil
                from django.core.files import File
                
                audio_dir = os.path.join(settings.MEDIA_ROOT, 'voiceprint_audio')
                if not os.path.exists(audio_dir):
                    os.makedirs(audio_dir)
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                random_str = str(uuid.uuid4())[:8]
                file_extension = os.path.splitext(file.name)[1]
                stored_filename = f'voiceprint_{timestamp}_{random_str}{file_extension}'
                stored_path = os.path.join(audio_dir, stored_filename)
                
                with open(stored_path, 'wb') as f:
                    with open(temp_file, 'rb') as temp_f:
                        f.write(temp_f.read())
                
                # 创建 Voiceprint
                voiceprint = Voiceprint.objects.create(
                    speaker=speaker,
                    name=None,
                    user=request.user,
                    feature=Voiceprint.feature_to_binary(vp_feature),
                    file_path=stored_path,  # 保留 file_path
                    source_type='manual'
                )
                
                # 正确地保存 audio_file（FileField）
                with open(stored_path, 'rb') as f:
                    django_file = File(f, name=stored_filename)
                    voiceprint.audio_file.save(stored_filename, django_file, save=True)
                
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return Response({
                "status": "success",
                "detail": f"说话人「{speaker_name}」创建成功",
                "speaker_id": speaker.id,
                "created_at": speaker.created_at.isoformat()
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"创建说话人失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Speaker 更新 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerUpdateView(APIView):
    """重命名说话人、更新头像"""
    @method_decorator(require_auth)
    def post(self, request):
        try:
            # 🌟 从 request.POST 取（因为是 form-data）
            print(f'[DEBUG] SpeakerUpdateView request.POST: {request.POST}')
            print(f'[DEBUG] request.FILES: {request.FILES}')
            
            sp_id = request.POST.get("id")
            new_name = request.POST.get("name", "").strip()
            
            print(f'[DEBUG] sp_id: {sp_id}, new_name: {new_name}')
            
            if not sp_id:
                return Response(
                    {"status": "failed", "detail": "说话人ID不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            update_details = []
            
            # 🌟 处理重命名
            if new_name:
                if Speaker.objects.filter(name=new_name, user=request.user).exclude(id=sp_id).exists():
                    return Response(
                        {"status": "failed", "detail": f"说话人名称「{new_name}」已存在"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                old_name = speaker.name
                speaker.name = new_name
                update_details.append(f"从「{old_name}」重命名为「{new_name}」")
            
            # 🌟 处理更新头像（可选）
            if 'avatar' in request.FILES:
                file = request.FILES['avatar']
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                
                if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                    return Response(
                        {"status": "failed", "detail": f"只支持图片格式：{allowed_extensions}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if file.size > 5 * 1024 * 1024:
                    return Response(
                        {"status": "failed", "detail": "图片大小不能超过5MB"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 删除旧头像
                if speaker.avatar:
                    try:
                        if os.path.exists(speaker.avatar.path):
                            os.remove(speaker.avatar.path)
                    except:
                        pass
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                random_str = str(uuid.uuid4())[:8]
                file_extension = os.path.splitext(file.name)[1]
                new_filename = f'speaker_avatar_{speaker.id}_{timestamp}_{random_str}{file_extension}'
                
                avatar_dir = os.path.join(settings.MEDIA_ROOT, 'speaker_avatars')
                if not os.path.exists(avatar_dir):
                    os.makedirs(avatar_dir)
                
                avatar_path = os.path.join(avatar_dir, new_filename)
                with open(avatar_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # 正确保存 FileField
                from django.core.files import File
                with open(avatar_path, 'rb') as f:
                    django_file = File(f, name=new_filename)
                    speaker.avatar.save(f'speaker_avatars/{new_filename}', django_file, save=False)
                update_details.append("头像已更新")
            
            speaker.save()
            
            return Response({
                "status": "success",
                "detail": "说话人信息已更新：" + "；".join(update_details) if update_details else "无变更",
                "speaker_id": speaker.id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"更新说话人失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Speaker 删除 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerDeleteView(APIView):
    @method_decorator(require_auth)
    def post(self, request):
        try:
            sp_id = request.data.get("id")
            if not sp_id:
                return Response(
                    {"status": "failed", "detail": "说话人ID不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            voiceprints = speaker.voiceprints.all()
            for vp in voiceprints:
                if vp.file_path and os.path.exists(vp.file_path):
                    try:
                        os.remove(vp.file_path)
                    except:
                        pass
                
                if vp.audio_file and os.path.exists(vp.audio_file.path):
                    try:
                        os.remove(vp.audio_file.path)
                    except:
                        pass
            
            sp_name = speaker.name
            speaker.delete()
            
            return Response({
                "status": "success",
                "detail": f"说话人「{sp_name}」删除成功",
                "speaker_id": sp_id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"删除说话人失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Speaker 头像上传 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerAvatarUploadView(APIView):
    @method_decorator(require_auth)
    def post(self, request, sp_id):
        try:
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if 'avatar' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传图片文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['avatar']
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                return Response(
                    {"status": "failed", "detail": f"仅支持图片格式：{allowed_extensions}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if file.size > 5 * 1024 * 1024:
                return Response(
                    {"status": "failed", "detail": "图片大小不能超过5MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if speaker.avatar:
                try:
                    if os.path.exists(speaker.avatar.path):
                        os.remove(speaker.avatar.path)
                except:
                    pass
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(file.name)[1]
            new_filename = f'speaker_avatar_{speaker.id}_{timestamp}_{random_str}{file_extension}'
            
            avatar_dir = os.path.join(settings.MEDIA_ROOT, 'speaker_avatars')
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir)
            
            avatar_path = os.path.join(avatar_dir, new_filename)
            with open(avatar_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            speaker.avatar.name = f'speaker_avatars/{new_filename}'
            speaker.save()
            
            return Response({
                "status": "success",
                "detail": "头像上传成功",
                "avatar_url": f"/media/speaker_avatars/{new_filename}"
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"头像上传失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Speaker 头像删除 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerAvatarDeleteView(APIView):
    @method_decorator(require_auth)
    def post(self, request, sp_id):
        try:
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if not speaker.avatar:
                return Response(
                    {"status": "failed", "detail": "该说话人没有头像"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                if os.path.exists(speaker.avatar.path):
                    os.remove(speaker.avatar.path)
            except:
                pass
            
            speaker.avatar = None
            speaker.save()
            
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

# ------------------- 删除 Speaker 的声纹 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerVoiceprintDeleteView(APIView):
    """删除 Speaker 的某条声纹，但不能删除该 Speaker 最早创建的那条 manual 声纹"""
    @method_decorator(require_auth)
    def post(self, request, sp_id, vp_id):
        try:
            print(f'[DEBUG] SpeakerVoiceprintDeleteView sp_id: {sp_id}, vp_id: {vp_id}')
            
            # 检查 Speaker 是否存在
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 检查 Voiceprint 是否存在且属于该 Speaker
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, speaker=speaker)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 🔒 核心限制：不能删除该 Speaker 最早创建的那条 manual 声纹！
            voiceprints = speaker.voiceprints.order_by('created_at')
            oldest_manual_vp = voiceprints.filter(source_type='manual').first()
            
            if oldest_manual_vp and voiceprint.id == oldest_manual_vp.id:
                return Response(
                    {"status": "failed", "detail": "不能删除该说话人最开始创建的声纹！"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 删除关联的音频文件
            if voiceprint.audio_file and os.path.exists(voiceprint.audio_file.path):
                try:
                    os.remove(voiceprint.audio_file.path)
                    print(f"已删除音频文件: {voiceprint.audio_file.path}")
                except Exception as e:
                    print(f"删除音频文件失败: {e}")
            
            if voiceprint.file_path and os.path.exists(voiceprint.file_path):
                try:
                    os.remove(voiceprint.file_path)
                    print(f"已删除音频文件: {voiceprint.file_path}")
                except Exception as e:
                    print(f"删除音频文件失败: {e}")
            
            voiceprint.delete()
            
            return Response({
                "status": "success",
                "detail": f"声纹删除成功",
                "voiceprint_id": vp_id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"删除声纹失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------- 给 Speaker 追加声纹 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerVoiceprintAddView(APIView):
    """给某个说话人追加新声纹"""
    @method_decorator(require_auth)
    def post(self, request, sp_id):
        try:
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 🌟 强制检查文件是否上传
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "必须上传音频文件才能追加声纹！"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            if not file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                return Response(
                    {"status": "failed", "detail": f"仅支持音频格式：{settings.ALLOWED_EXTENSIONS}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            temp_filename = f"vp_temp_{uuid.uuid4()}_{file.name}"
            temp_file = os.path.join(settings.TEMP_DIR, temp_filename)
            with open(temp_file, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            vp_feature = extract_voiceprint_feature(temp_file)
            
            if vp_feature is None:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return Response(
                    {"status": "failed", "detail": "声纹特征提取失败"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 保存文件到 media/voiceprint_audio/
            from django.core.files import File
            
            audio_dir = os.path.join(settings.MEDIA_ROOT, 'voiceprint_audio')
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(file.name)[1]
            stored_filename = f'voiceprint_{timestamp}_{random_str}{file_extension}'
            stored_path = os.path.join(audio_dir, stored_filename)
            
            with open(stored_path, 'wb') as f:
                with open(temp_file, 'rb') as temp_f:
                    f.write(temp_f.read())
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            # 🌟 直接创建 Voiceprint，不再调用 append_voiceprint（避免混淆）
            voiceprint = Voiceprint.objects.create(
                speaker=speaker,
                user=request.user,
                feature=Voiceprint.feature_to_binary(vp_feature),
                file_path=stored_path,
                source_type='manual'
            )
            
            # 正确保存 audio_file
            with open(stored_path, 'rb') as f:
                django_file = File(f, name=stored_filename)
                voiceprint.audio_file.save(stored_filename, django_file, save=True)
            
            return Response({
                "status": "success",
                "detail": f"声纹追加成功",
                "speaker_id": speaker.id,
                "voiceprint_id": voiceprint.id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"追加声纹失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------- 更新 Speaker 指定的声纹 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerVoiceprintUpdateView(APIView):
    """更新 Speaker 指定的声纹（上传新音频替换）"""
    @method_decorator(require_auth)
    def post(self, request, sp_id, vp_id):
        try:
            print(f'[DEBUG] SpeakerVoiceprintUpdateView sp_id: {sp_id}, vp_id: {vp_id}')
            print(f'[DEBUG] request.FILES: {request.FILES}')
            
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, speaker=speaker)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 🔒 核心限制：不能更新该说话人最早创建的那条 manual！
            voiceprints = speaker.voiceprints.order_by('created_at')
            oldest_manual_vp = voiceprints.filter(source_type='manual').first()
            
            if oldest_manual_vp and voiceprint.id == oldest_manual_vp.id:
                return Response(
                    {"status": "failed", "detail": "不能修改该说话人最开始创建的声纹！"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查文件
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "必须上传新的音频文件！"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            if not file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                return Response(
                    {"status": "failed", "detail": f"仅支持音频格式：{settings.ALLOWED_EXTENSIONS}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 保存新的临时文件，提取特征
            temp_filename = f"vp_temp_{uuid.uuid4()}_{file.name}"
            temp_file = os.path.join(settings.TEMP_DIR, temp_filename)
            with open(temp_file, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            vp_feature = extract_voiceprint_feature(temp_file)
            
            if vp_feature is None:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return Response(
                    {"status": "failed", "detail": "声纹特征提取失败"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 准备保存新的音频文件到 media/voiceprint_audio/
            from django.core.files import File
            
            audio_dir = os.path.join(settings.MEDIA_ROOT, 'voiceprint_audio')
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(file.name)[1]
            stored_filename = f'voiceprint_{timestamp}_{random_str}{file_extension}'
            stored_path = os.path.join(audio_dir, stored_filename)
            
            with open(stored_path, 'wb') as f:
                with open(temp_file, 'rb') as temp_f:
                    f.write(temp_f.read())
            
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            # 删除旧的音频文件
            if voiceprint.file_path:
                try:
                    if os.path.exists(voiceprint.file_path):
                        os.remove(voiceprint.file_path)
                        print(f"已删除旧版音频文件: {voiceprint.file_path}")
                except:
                    pass
            
            # 更新声纹信息
            voiceprint.feature = Voiceprint.feature_to_binary(vp_feature)
            voiceprint.file_path = stored_path
            
            # 正确保存新的 audio_file
            with open(stored_path, 'rb') as f:
                django_file = File(f, name=stored_filename)
                voiceprint.audio_file.save(stored_filename, django_file, save=True)
            
            return Response({
                "status": "success",
                "detail": f"声纹更新成功",
                "speaker_id": speaker.id,
                "voiceprint_id": voiceprint.id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"更新声纹失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------- Speaker 声纹音频获取 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SpeakerVoiceprintAudioView(APIView):
    """获取 Speaker 声纹音频文件（用于前端播放）"""
    @method_decorator(require_auth)
    def get(self, request, sp_id, vp_id):
        try:
            # 检查 Speaker 是否存在
            try:
                speaker = Speaker.objects.get(id=sp_id, user=request.user)
            except Speaker.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{sp_id}的说话人"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 检查 Voiceprint 是否存在且属于该 Speaker
            try:
                voiceprint = Voiceprint.objects.get(id=vp_id, speaker=speaker)
            except Voiceprint.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": f"未找到ID为{vp_id}的声纹"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 检查文件是否存在（优先 audio_file，回退 file_path）
            audio_path = None
            if voiceprint.audio_file and os.path.exists(voiceprint.audio_file.path):
                audio_path = voiceprint.audio_file.path
            elif voiceprint.file_path and os.path.exists(voiceprint.file_path):
                audio_path = voiceprint.file_path
            
            if not audio_path:
                return Response(
                    {"status": "failed", "detail": "声纹文件不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 读取文件内容并返回
            from django.http import FileResponse
            import mimetypes
            
            # 确定文件的MIME类型
            mime_type, _ = mimetypes.guess_type(audio_path)
            if not mime_type:
                mime_type = 'audio/wav'
            
            # 直接使用文件路径创建FileResponse
            try:
                response = FileResponse(open(audio_path, 'rb'), content_type=mime_type)
                # 设置文件名
                filename = os.path.basename(audio_path)
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
