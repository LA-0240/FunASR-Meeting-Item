from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from ..models import User
from ..auth_utils import create_token, require_auth
import traceback

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
                "created_at": user.created_at.isoformat()
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取用户信息失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )