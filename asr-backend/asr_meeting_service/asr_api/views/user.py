from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from ..models import User
from ..auth_utils import create_token, require_auth
import traceback
import os
import uuid
from datetime import datetime

# ------------------- 用户注册接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(APIView):
    def post(self, request):
        """用户注册"""
        try:
            username = request.data.get("username", "").strip()
            email = request.data.get("email", "").strip()
            password = request.data.get("password", "").strip()
            
            if not username or not email or not password:
                return Response(
                    {"status": "failed", "detail": "用户名、邮箱和密码不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 检查用户名是否已存在
            if User.objects.filter(username=username).exists():
                return Response(
                    {"status": "failed", "detail": "用户名已存在"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 检查邮箱是否已存在
            if User.objects.filter(email=email).exists():
                return Response(
                    {"status": "failed", "detail": "邮箱已存在"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 创建用户
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # 创建令牌
            token = create_token(user)
            
            return Response({
                "status": "success",
                "detail": "注册成功",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "token": token
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"注册失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 用户登录接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    def post(self, request):
        """用户登录"""
        try:
            username = request.data.get("username", "").strip()
            password = request.data.get("password", "").strip()
            
            if not username or not password:
                return Response(
                    {"status": "failed", "detail": "用户名和密码不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 验证用户
            user = authenticate(username=username, password=password)
            if not user:
                return Response(
                    {"status": "failed", "detail": "用户名或密码错误"},
                    status=HTTP_401_UNAUTHORIZED
                )
            
            # 创建令牌
            token = create_token(user)
            
            return Response({
                "status": "success",
                "detail": "登录成功",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "token": token
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"登录失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 用户退出接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(APIView):
    @method_decorator(require_auth)
    def post(self, request):
        """用户退出"""
        try:
            # 删除用户令牌
            request.user.auth_token.delete()
            
            return Response({
                "status": "success",
                "detail": "退出成功"
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"退出失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 用户信息接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class UserProfileView(APIView):
    @method_decorator(require_auth)
    def get(self, request):
        """获取用户信息"""
        try:
            user = request.user
            
            return Response({
                "status": "success",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "avatar_url": user.avatar.url if user.avatar else None,
                "created_at": user.created_at.isoformat()
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取用户信息失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )
    
    @method_decorator(require_auth)
    def put(self, request):
        """更新用户信息"""
        try:
            user = request.user
            
            # 获取 Content-Type 检查
            print(f"Content-Type: {request.content_type}")
            
            username = ""
            email = ""
            password = ""
            
            # 优先尝试解析数据
            try:
                if hasattr(request, 'data') and request.data:
                    if hasattr(request.data, 'get'):
                        # JSON格式
                        username = request.data.get("username", "").strip()
                        email = request.data.get("email", "").strip()
                        password = request.data.get("password", "").strip()
                    elif isinstance(request.data, dict):
                        # 字典格式
                        username = request.data.get("username", "").strip()
                        email = request.data.get("email", "").strip()
                        password = request.data.get("password", "").strip()
            except Exception:
                pass
            
            # 尝试从 POST 中获取
            if not username and not email and not password and hasattr(request, 'POST'):
                username = request.POST.get("username", "").strip()
                email = request.POST.get("email", "").strip()
                password = request.POST.get("password", "").strip()
            
            # 验证并更新用户名
            if username:
                if username != user.username and User.objects.filter(username=username).exists():
                    return Response(
                        {"status": "failed", "detail": "用户名已存在"},
                        status=HTTP_400_BAD_REQUEST
                    )
                user.username = username
            
            # 验证并更新邮箱
            if email:
                if email != user.email and User.objects.filter(email=email).exists():
                    return Response(
                        {"status": "failed", "detail": "邮箱已存在"},
                        status=HTTP_400_BAD_REQUEST
                    )
                user.email = email
            
            # 更新密码
            if password:
                user.set_password(password)
            
            # 保存用户
            user.save()
            
            return Response({
                "status": "success",
                "detail": "用户信息更新成功",
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"更新用户信息失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 头像上传接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class UserAvatarUploadView(APIView):
    @method_decorator(require_auth)
    def post(self, request):
        """上传用户头像"""
        try:
            user = request.user
            
            # 检查是否有上传的文件
            if 'avatar' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "请上传头像文件"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            avatar_file = request.FILES['avatar']
            
            # 检查文件类型
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if avatar_file.content_type not in allowed_types:
                return Response(
                    {"status": "failed", "detail": "只支持 JPG、PNG、GIF 格式的图片"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 检查文件大小（限制为 5MB）
            if avatar_file.size > 5 * 1024 * 1024:
                return Response(
                    {"status": "failed", "detail": "头像文件大小不能超过 5MB"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 删除旧头像
            if user.avatar and user.avatar.path and os.path.exists(user.avatar.path):
                try:
                    os.remove(user.avatar.path)
                except Exception:
                    pass
            
            # 生成唯一文件名
            ext = avatar_file.name.split('.')[-1].lower()
            filename = f"avatar_{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # 保存新头像
            user.avatar.save(filename, avatar_file, save=True)
            
            # 获取头像 URL
            avatar_url = user.avatar.url if user.avatar else None
            
            return Response({
                "status": "success",
                "detail": "头像上传成功",
                "avatar_url": avatar_url
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"头像上传失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 删除头像接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class UserAvatarDeleteView(APIView):
    @method_decorator(require_auth)
    def delete(self, request):
        """删除用户头像"""
        try:
            user = request.user
            
            # 删除头像文件
            if user.avatar and user.avatar.path and os.path.exists(user.avatar.path):
                try:
                    os.remove(user.avatar.path)
                except Exception:
                    pass
            
            # 清空头像字段
            user.avatar = None
            user.save()
            
            return Response({
                "status": "success",
                "detail": "头像删除成功"
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"头像删除失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )