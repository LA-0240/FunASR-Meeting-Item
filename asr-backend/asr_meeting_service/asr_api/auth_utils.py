"""
用户认证工具模块
提供令牌创建、用户验证和认证装饰器等功能
"""
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED

def create_token(user):
    """创建或获取用户Token
    Args:
        user: 用户对象
    Returns:
        str: 令牌字符串
    """
    token, created = Token.objects.get_or_create(user=user)
    return token.key

def authenticate_user(username, password):
    """验证用户凭据并返回用户和令牌
    Args:
        username: 用户名
        password: 密码
    Returns:
        tuple: (用户对象, 令牌字符串)，验证失败返回(None, None)
    """
    user = authenticate(username=username, password=password)
    if user:
        token = create_token(user)
        return user, token
    return None, None

def get_user_from_token(token):
    """从Token获取对应的用户
    Args:
        token: 令牌字符串
    Returns:
        User: 用户对象，找不到则返回None
    """
    try:
        token_obj = Token.objects.get(key=token)
        return token_obj.user
    except Token.DoesNotExist:
        return None

def require_auth(view_func):
    """API认证装饰器，验证用户Token
    Args:
        view_func: 视图函数
    Returns:
        function: 包装后的视图函数
    """
    def wrapper(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if not token:
            return Response({"status": "failed", "detail": "未提供认证令牌"}, status=HTTP_401_UNAUTHORIZED)
        
        user = get_user_from_token(token)
        if not user:
            return Response({"status": "failed", "detail": "无效的认证令牌"}, status=HTTP_401_UNAUTHORIZED)
        
        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapper