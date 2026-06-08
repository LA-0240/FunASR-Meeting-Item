"""
基础API视图模块
提供健康检查等基础接口
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime

# ------------------- 基础接口（健康检查） -------------------
class HealthCheckView(APIView):
    """
    健康检查视图
    用于检查服务是否正常运行
    """
    def get(self, request):
        """
        服务健康检查，对齐FastAPI的/接口
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Response: 包含服务状态、功能列表的响应
        """
        return Response({
            "status": "healthy",
            "service": "基于LLM的会议纪要智能生成系统",
            "timestamp": datetime.now().isoformat(),
            "features": ["语音|视频---转文字（带时间标点/说话人）", "会议纪要生成","会议摘要生成","Word文档导出(转写、纪要、摘要)"]
        })