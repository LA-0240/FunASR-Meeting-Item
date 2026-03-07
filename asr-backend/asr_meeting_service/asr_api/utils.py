# 确保导入路径和拼写完全正确
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """自定义异常处理，对齐FastAPI的异常返回格式"""
    response = exception_handler(exc, context)

    # 如果DRF未处理异常，手动封装
    if response is None:
        if isinstance(exc, Exception):
            return Response(
                {"detail": f"服务器内部错误：{str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return None

    # 统一异常返回格式
    if response.status_code == 400:
        response.data = {"status": "failed", "detail": response.data}
    elif response.status_code == 500:
        response.data = {"status": "failed", "detail": response.data.get("detail", "服务器内部错误")}
    
    return response