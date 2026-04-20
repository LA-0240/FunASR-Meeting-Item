from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED

def create_token(user):
    """创建或获取用户令牌"""
    token, created = Token.objects.get_or_create(user=user)
    return token.key

def authenticate_user(username, password):
    """验证用户并返回令牌"""
    user = authenticate(username=username, password=password)
    if user:
        token = create_token(user)
        return user, token
    return None, None

def get_user_from_token(token):
    """从令牌获取用户"""
    try:
        token_obj = Token.objects.get(key=token)
        return token_obj.user
    except Token.DoesNotExist:
        return None

def require_auth(view_func):
    """认证装饰器"""
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