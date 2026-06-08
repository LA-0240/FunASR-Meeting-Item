"""
Prompt模板管理视图模块
提供Prompt模板的增删改查功能
"""
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import traceback
from ..models import Prompt
from ..auth_utils import require_auth

# ------------------- Prompt 列表 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class PromptListView(APIView):
    """获取Prompt模板列表视图：获取默认模板和用户自定义模板"""
    @method_decorator(require_auth)  # 添加认证装饰器
    def get(self, request):
        """
        获取Prompt模板列表
        
        Args:
            request: HTTP请求对象，包含可选的搜索参数
            
        Returns:
            Response: 包含Prompt列表的响应
        """
        try:
            # 获取查询参数
            name = request.query_params.get('name', '').strip()
            category = request.query_params.get('category', '').strip()
            template_type = request.query_params.get('template_type', '').strip()
            
            # 获取默认模板和当前用户的自定义模板
            default_prompts = Prompt.objects.filter(category='default')
            custom_prompts = Prompt.objects.filter(category='custom', user=request.user)
            
            # 应用过滤条件
            if name:
                default_prompts = default_prompts.filter(name__icontains=name)
                custom_prompts = custom_prompts.filter(name__icontains=name)
            
            if category:
                default_prompts = default_prompts.filter(category=category)
                custom_prompts = custom_prompts.filter(category=category)
            
            if template_type:
                default_prompts = default_prompts.filter(template_type=template_type)
                custom_prompts = custom_prompts.filter(template_type=template_type)
            
            # 构建响应数据
            prompts = []
            
            # 添加默认模板
            for prompt in default_prompts:
                prompts.append({
                    "id": prompt.id,
                    "name": prompt.name,
                    "system_prompt": prompt.system_prompt,
                    "user_prompt": prompt.user_prompt,
                    "category": prompt.category,
                    "template_type": prompt.template_type,
                    "created_at": prompt.created_at.isoformat(),
                    "updated_at": prompt.updated_at.isoformat()
                })
            
            # 添加用户自定义模板
            for prompt in custom_prompts:
                prompts.append({
                    "id": prompt.id,
                    "name": prompt.name,
                    "system_prompt": prompt.system_prompt,
                    "user_prompt": prompt.user_prompt,
                    "category": prompt.category,
                    "template_type": prompt.template_type,
                    "created_at": prompt.created_at.isoformat(),
                    "updated_at": prompt.updated_at.isoformat()
                })
            
            return Response({
                "status": "success",
                "count": len(prompts),
                "prompts": prompts
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取模板列表失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 添加 Prompt -------------------
@method_decorator(csrf_exempt, name='dispatch')
class PromptAddView(APIView):
    """添加Prompt模板视图：创建新的自定义Prompt模板"""
    @method_decorator(require_auth)  # 添加认证装饰器
    def post(self, request):
        """
        添加自定义Prompt模板
        
        Args:
            request: HTTP请求对象，包含Prompt名称和内容
            
        Returns:
            Response: 添加结果
        """
        try:
            # 1. 提取参数
            name = request.data.get("name", "").strip()
            system_prompt = request.data.get("system_prompt", "").strip()
            user_prompt = request.data.get("user_prompt", "").strip()
            template_type = request.data.get("template_type", "").strip()
            
            # 2. 校验参数
            if not name:
                return Response(
                    {"status": "failed", "detail": "模板名称不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not system_prompt:
                return Response(
                    {"status": "failed", "detail": "系统提示词不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not user_prompt:
                return Response(
                    {"status": "failed", "detail": "用户提示词不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not template_type:
                return Response(
                    {"status": "failed", "detail": "模板类型不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if template_type not in ['summary', 'abstract']:
                return Response(
                    {"status": "failed", "detail": "模板类型必须是 summary 或 abstract"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 检查名称是否已存在（针对当前用户）
            if Prompt.objects.filter(name=name, user=request.user).exists():
                return Response(
                    {"status": "failed", "detail": f"模板名称「{name}」已存在"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. 创建模板
            prompt = Prompt(
                name=name,
                user=request.user,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                category='custom',
                template_type=template_type
            )
            prompt.save()
            
            return Response({
                "status": "success",
                "detail": f"模板「{name}」添加成功",
                "prompt_id": prompt.id,
                "created_at": prompt.created_at.isoformat()
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"添加模板失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 更新 Prompt -------------------
@method_decorator(csrf_exempt, name='dispatch')
class PromptUpdateView(APIView):
    """更新Prompt模板视图：编辑现有的Prompt模板"""
    @method_decorator(require_auth)  # 添加认证装饰器
    def put(self, request, prompt_id):
        """
        更新自定义Prompt模板
        
        Args:
            request: HTTP请求对象，包含Prompt名称和内容
            prompt_id: Prompt模板ID
            
        Returns:
            Response: 更新结果
        """
        try:
            # 1. 提取参数
            name = request.data.get("name", "").strip()
            system_prompt = request.data.get("system_prompt", "").strip()
            user_prompt = request.data.get("user_prompt", "").strip()
            
            # 2. 校验参数
            if not name:
                return Response(
                    {"status": "failed", "detail": "模板名称不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not system_prompt:
                return Response(
                    {"status": "failed", "detail": "系统提示词不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not user_prompt:
                return Response(
                    {"status": "failed", "detail": "用户提示词不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 检查模板是否存在且属于当前用户
            try:
                prompt = Prompt.objects.get(id=prompt_id, user=request.user, category='custom')
            except Prompt.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "模板不存在或无权限"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 4. 检查新名称是否重复（针对当前用户）
            if Prompt.objects.filter(name=name, user=request.user).exclude(id=prompt_id).exists():
                return Response(
                    {"status": "failed", "detail": f"模板名称「{name}」已存在"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 5. 更新模板
            old_name = prompt.name
            prompt.name = name
            prompt.system_prompt = system_prompt
            prompt.user_prompt = user_prompt
            prompt.save()
            
            return Response({
                "status": "success",
                "detail": f"模板「{old_name}」更新成功",
                "prompt_id": prompt.id,
                "updated_at": prompt.updated_at.isoformat()
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"更新模板失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 删除 Prompt -------------------
@method_decorator(csrf_exempt, name='dispatch')
class PromptDeleteView(APIView):
    """删除Prompt模板视图：删除用户自定义的Prompt模板"""
    @method_decorator(require_auth)  # 添加认证装饰器
    def delete(self, request, prompt_id):
        """
        删除自定义Prompt模板
        
        Args:
            request: HTTP请求对象
            prompt_id: Prompt模板ID
            
        Returns:
            Response: 删除结果
        """
        try:
            # 1. 检查模板是否存在且属于当前用户
            try:
                prompt = Prompt.objects.get(id=prompt_id, user=request.user, category='custom')
            except Prompt.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "模板不存在或无权限"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 2. 删除模板
            prompt_name = prompt.name
            prompt.delete()
            
            return Response({
                "status": "success",
                "detail": f"模板「{prompt_name}」删除成功",
                "prompt_id": prompt_id
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"删除模板失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 复制 Prompt -------------------
@method_decorator(csrf_exempt, name='dispatch')
class PromptCopyView(APIView):
    """复制Prompt模板视图：获取默认模板内容用于复制"""
    @method_decorator(require_auth)  # 添加认证装饰器
    def post(self, request, prompt_id):
        """
        获取默认Prompt模板内容（用于前端复制到编辑窗口）
        
        Args:
            request: HTTP请求对象
            prompt_id: Prompt模板ID
            
        Returns:
            Response: 包含Prompt内容的响应
        """
        try:
            # 1. 检查默认模板是否存在
            try:
                source_prompt = Prompt.objects.get(id=prompt_id, category='default')
            except Prompt.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "默认模板不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 2. 返回模板内容，供前端复制到编辑窗口
            return Response({
                "status": "success",
                "detail": "模板内容获取成功",
                "name": source_prompt.name,
                "system_prompt": source_prompt.system_prompt,
                "user_prompt": source_prompt.user_prompt
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取模板内容失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
