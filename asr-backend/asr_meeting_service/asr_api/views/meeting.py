"""
会议管理视图模块
提供会议纪要生成、会议摘要生成、分段生成、纪要编辑等功能
"""
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.permissions import IsAuthenticated  # 添加这一行
from openai import OpenAI
import time
import uuid
from datetime import datetime
import traceback
import os
import subprocess
import json
from ..models import UploadedFile, MeetingSummary, Transcription, Prompt, MeetingSegment
from ..auth_utils import require_auth

# 导入语义分段（项目新增）
from .semantic_segmentation import semantic_segment_transcription

# 初始化LLM客户端
llm_client = OpenAI(
    api_key=settings.LLM_CONFIG["api_key"],
    base_url=settings.LLM_CONFIG["base_url"]
)

# ------------------- 会议纪要生成接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingSummaryView(APIView):
    """会议纪要生成视图：使用LLM生成结构化会议纪要"""
    @method_decorator(require_auth)
    def post(self, request):
        """
        基于文件ID生成结构化会议纪要
        
        Args:
            request: HTTP请求对象，包含文件ID、Prompt ID等参数
            
        Returns:
            Response: 包含生成的会议纪要的响应
        """
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            output_format = request.data.get("output_format", "txt")
            custom_system_prompt = request.data.get("custom_system_prompt", None)
            custom_user_prompt = request.data.get("custom_user_prompt", None)
            prompt_id = request.data.get("prompt_id", None)
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
            
            # 4. 检查逐字稿是否存在
            try:
                transcription = Transcription.objects.get(file=file)
                if not transcription.transcription_text:
                    return Response(
                        {"status": "failed", "detail": "逐字稿不存在或内容为空"},
                        status=HTTP_404_NOT_FOUND
                    )
                transcription_text = transcription.transcription_text
            except Transcription.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "逐字稿不存在"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 4. 检查是否已生成纪要
            if file_id and not force_regenerate:
                try:
                    existing_summary = MeetingSummary.objects.get(file=file)
                    return Response({
                        "status": "success",
                        "detail": "会议纪要已存在",
                        "meeting_summary": existing_summary.summary_text,
                        "is_customized": existing_summary.is_customized,
                        "timestamp": existing_summary.updated_at.strftime("%Y%m%d_%H%M%S")
                    }, status=HTTP_200_OK)
                except MeetingSummary.DoesNotExist:
                    pass
            
            # 5. 处理Prompt模板
            # 优先级：自定义 > 模板 > 默认
            template_system_prompt = None
            template_user_prompt = None
            
            # 如果提供了prompt_id，使用对应的模板
            if prompt_id:
                try:
                    # 检查模板是否存在
                    prompt = Prompt.objects.get(id=prompt_id)
                    # 验证权限：如果是自定义模板，必须属于当前用户
                    if prompt.category == 'custom' and prompt.user != request.user:
                        return Response(
                            {"status": "failed", "detail": "模板不存在或无权限"},
                            status=HTTP_404_NOT_FOUND
                        )
                    # 验证模板类型：必须是纪要模板
                    if prompt.template_type != 'summary':
                        return Response(
                            {"status": "failed", "detail": "请选择纪要类型的模板"},
                            status=HTTP_400_BAD_REQUEST
                        )
                    # 使用模板的prompt
                    template_system_prompt = prompt.system_prompt
                    template_user_prompt = prompt.user_prompt
                except Prompt.DoesNotExist:
                    return Response(
                        {"status": "failed", "detail": "模板不存在"},
                        status=HTTP_404_NOT_FOUND
                    )
            
            # 6. 定义默认Prompt
            default_system_prompt = """你是专业的会议纪要生成助手，需严格按照以下要求处理：
1. 结构化提取信息：
   - 会议主题（精准概括核心议题）
   - 参与发言人列表（去重）
   - 核心讨论内容（按发言人分类整理，保留关键观点）
   - 关键结论/决议（明确会议达成的决策）
   - 待办事项（Action Items）：必须提取【任务-负责人】，若无截止时间则标注“未指定”，不要省略
2. 格式要求：
   - 使用层级标题（如## 会议主题）、项目符号/编号
   - 待办事项单独成节，突出显示
   - 语言简洁、逻辑清晰，无冗余信息
3. 特殊处理：
   - 多人对话严格区分发言人，避免混淆
   - 只要有任务，就必须列出来，不允许写“无待办事项”
   - 转录文本不完整时，基于已有内容合理归纳"""

            default_user_prompt = f"""请基于以下会议转录文本生成结构化会议纪要：

【会议转录文本】
{transcription_text}

【输出要求】
1. 严格遵循上述系统提示的结构和格式
2. 重点突出待办事项的"任务-负责人-截止时间"三元组
3. 仅输出纪要文本，无需额外解释或说明
4. 确保语言通顺，无语法错误，信息无遗漏"""
            
            # 7. 优先级：自定义 > 模板 > 默认
            final_system_prompt = custom_system_prompt if (custom_system_prompt and custom_system_prompt.strip()) else (
                template_system_prompt if template_system_prompt else default_system_prompt
            )
            
            # 处理user_prompt中的{transcription_text}占位符
            if custom_user_prompt and custom_user_prompt.strip():
                final_user_prompt = custom_user_prompt.replace('{transcription_text}', transcription_text)
            elif template_user_prompt:
                final_user_prompt = template_user_prompt.replace('{transcription_text}', transcription_text)
            else:
                final_user_prompt = default_user_prompt
            
            # 7. 调用LLM
            response = llm_client.chat.completions.create(
                model=settings.LLM_CONFIG["model_name"],
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": final_user_prompt}
                ],
                stream=False,
                temperature=0.3,
                max_tokens=4000,
                timeout=300
            )
            
            # 8. 提取结果
            meeting_minutes = response.choices[0].message.content.strip()
            
            # 9. 保存纪要到数据库
            if file_id:
                try:
                    # 如果已存在纪要且强制重新生成，更新它
                    summary = MeetingSummary.objects.get(file=file)
                    summary.summary_text = meeting_minutes
                    summary.is_customized = False
                    summary.save()
                except MeetingSummary.DoesNotExist:
                    # 如果不存在，创建新的
                    summary = MeetingSummary(
                        file=file,
                        summary_text=meeting_minutes,
                        is_customized=False
                    )
                    summary.save()
                
                # 更新文件状态
                file.status = "processed"
                file.save()
            
            return Response({
                "status": "success",
                "meeting_minutes": meeting_minutes,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "output_format": output_format,
                "used_system_prompt": final_system_prompt,
                "used_user_prompt": final_user_prompt,
                "is_customized": False
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"纪要生成失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 会议摘要生成接口（轻量化） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingAbstractView(APIView):
    """会议摘要生成视图：使用LLM生成轻量化会议摘要"""
    @method_decorator(require_auth)
    def post(self, request):
        """
        基于文件ID生成轻量化会议摘要（核心要点提炼）
        
        Args:
            request: HTTP请求对象，包含文件ID、摘要长度等参数
            
        Returns:
            Response: 包含生成的会议摘要的响应
        """
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            abstract_length = request.data.get("abstract_length", "medium")  # short/medium/long
            custom_system_prompt = request.data.get("custom_system_prompt", None)
            custom_user_prompt = request.data.get("custom_user_prompt", None)
            prompt_id = request.data.get("prompt_id", None)
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
            
            # 4. 检查逐字稿是否存在
            try:
                transcription = Transcription.objects.get(file=file)
                if not transcription.transcription_text:
                    return Response(
                        {"status": "failed", "detail": "逐字稿不存在或内容为空"},
                        status=HTTP_404_NOT_FOUND
                    )
                transcription_text = transcription.transcription_text
            except Transcription.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "逐字稿不存在"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 6. 定义长度对应的字数限制
            length_config = {
                "short": "100-200字",
                "medium": "200-400字",
                "long": "400-600字"
            }
            target_length = length_config.get(abstract_length, "200-400字")
            
            # 5. 检查是否已生成摘要
            if file_id and not force_regenerate:
                try:
                    existing_summary = MeetingSummary.objects.get(file=file)
                    if existing_summary.abstract_text:
                        return Response({
                            "status": "success",
                            "detail": "会议摘要已存在",
                            "meeting_abstract": existing_summary.abstract_text,
                            "timestamp": existing_summary.updated_at.strftime("%Y%m%d_%H%M%S"),
                            "abstract_length": abstract_length,
                            "target_word_count": target_length
                        }, status=HTTP_200_OK)
                except MeetingSummary.DoesNotExist:
                    pass
            
            # 6. 处理Prompt模板
            # 优先级：自定义 > 模板 > 默认
            template_system_prompt = None
            template_user_prompt = None
            
            # 如果提供了prompt_id，使用对应的模板
            if prompt_id:
                try:
                    # 检查模板是否存在
                    prompt = Prompt.objects.get(id=prompt_id)
                    # 验证权限：如果是自定义模板，必须属于当前用户
                    if prompt.category == 'custom' and prompt.user != request.user:
                        return Response(
                            {"status": "failed", "detail": "模板不存在或无权限"},
                            status=HTTP_404_NOT_FOUND
                        )
                    # 验证模板类型：必须是摘要模板
                    if prompt.template_type != 'abstract':
                        return Response(
                            {"status": "failed", "detail": "请选择摘要类型的模板"},
                            status=HTTP_400_BAD_REQUEST
                        )
                    # 使用模板的prompt
                    template_system_prompt = prompt.system_prompt
                    template_user_prompt = prompt.user_prompt
                except Prompt.DoesNotExist:
                    return Response(
                        {"status": "failed", "detail": "模板不存在"},
                        status=HTTP_404_NOT_FOUND
                    )
            
            # 7. 定义默认Prompt（轻量化摘要）
            default_system_prompt = f"""你是专业的会议摘要生成助手，需严格按照以下要求处理：
1. 核心要求：
   - 仅提炼会议最核心的信息，拒绝冗余内容
   - 保留会议的核心议题、关键结论、重要待办
   - 语言高度凝练，符合{target_length}的字数要求
2. 格式要求：
   - 纯文本段落形式，无需层级标题和列表
   - 逻辑连贯，语句通顺，无语法错误
   - 不添加任何额外解释性文字"""

            default_user_prompt = f"""请基于以下会议转录文本生成轻量化会议摘要：

【会议转录文本】
{transcription_text}

【输出要求】
1. 严格遵循上述系统提示的字数要求（{target_length}）
2. 仅输出摘要文本，无需额外解释或说明
3. 确保覆盖核心议题、关键结论、重要待办
4. 语言简洁凝练，符合正式会议摘要的表达习惯"""
            
            # 8. 优先级：自定义 > 模板 > 默认
            final_system_prompt = custom_system_prompt if (custom_system_prompt and custom_system_prompt.strip()) else (
                template_system_prompt if template_system_prompt else default_system_prompt
            )
            
            # 处理user_prompt中的{transcription_text}占位符
            if custom_user_prompt and custom_user_prompt.strip():
                final_user_prompt = custom_user_prompt.replace('{transcription_text}', transcription_text)
            elif template_user_prompt:
                final_user_prompt = template_user_prompt.replace('{transcription_text}', transcription_text)
            else:
                final_user_prompt = default_user_prompt
            
            # 7. 调用LLM生成摘要
            response = llm_client.chat.completions.create(
                model=settings.LLM_CONFIG["model_name"],
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": final_user_prompt}
                ],
                stream=False,
                temperature=0.2,  # 更低的温度保证摘要的准确性
                max_tokens=1000,
                timeout=300
            )
            
            # 8. 提取结果
            meeting_abstract = response.choices[0].message.content.strip()
            
            # 9. 更新数据库中的摘要
            if file_id:
                try:
                    summary = MeetingSummary.objects.get(file=file)
                    summary.abstract_text = meeting_abstract
                    summary.save()
                except MeetingSummary.DoesNotExist:
                    # 如果MeetingSummary不存在，创建新记录
                    summary = MeetingSummary(
                        file=file,
                        summary_text="",
                        abstract_text=meeting_abstract,
                        is_customized=False
                    )
                    summary.save()
            
            return Response({
                "status": "success",
                "meeting_abstract": meeting_abstract,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "abstract_length": abstract_length,
                "target_word_count": target_length,
                "used_system_prompt": final_system_prompt,
                "used_user_prompt": final_user_prompt
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"摘要生成失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )



# ------------------- 获取会议纪要接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class GetMeetingSummaryView(APIView):
    """获取会议纪要视图：获取已生成的会议纪要"""
    @method_decorator(require_auth)
    def get(self, request):
        """
        获取文件的会议纪要
        
        Args:
            request: HTTP请求对象，包含文件ID参数
            
        Returns:
            Response: 包含会议纪要的响应
        """
        try:
            # 1. 提取请求参数
            file_id = request.query_params.get("file_id")
            
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
            
            # 4. 检查是否已生成纪要
            try:
                existing_summary = MeetingSummary.objects.get(file=file)
                return Response({
                    "status": "success",
                    "meeting_summary": existing_summary.summary_text or "",
                    "is_customized": existing_summary.is_customized,
                    "timestamp": existing_summary.updated_at.strftime("%Y%m%d_%H%M%S")
                }, status=HTTP_200_OK)
            except MeetingSummary.DoesNotExist:
                # 如果记录不存在，返回空内容而不是404
                return Response({
                    "status": "success",
                    "meeting_summary": "",
                    "is_customized": False,
                    "timestamp": ""
                }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取会议纪要失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 获取会议摘要接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class GetMeetingAbstractView(APIView):
    """获取会议摘要视图：获取已生成的会议摘要"""
    @method_decorator(require_auth)
    def get(self, request):
        """
        获取文件的会议摘要
        
        Args:
            request: HTTP请求对象，包含文件ID参数
            
        Returns:
            Response: 包含会议摘要的响应
        """
        try:
            # 1. 提取请求参数
            file_id = request.query_params.get("file_id")
            
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
            
            # 4. 检查是否已生成摘要
            try:
                existing_summary = MeetingSummary.objects.get(file=file)
                return Response({
                    "status": "success",
                    "meeting_abstract": existing_summary.abstract_text or "",
                    "timestamp": existing_summary.updated_at.strftime("%Y%m%d_%H%M%S")
                }, status=HTTP_200_OK)
            except MeetingSummary.DoesNotExist:
                # 如果记录不存在，返回空内容而不是404
                return Response({
                    "status": "success",
                    "meeting_abstract": "",
                    "timestamp": ""
                }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取会议摘要失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 会议纪要编辑接口（分离） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingSummaryUpdateView(APIView):
    """会议纪要更新视图：编辑已生成的会议纪要"""
    @method_decorator(require_auth)
    def put(self, request):
        """
        更新会议纪要
        
        Args:
            request: HTTP请求对象，包含文件ID和纪要文本
            
        Returns:
            Response: 更新结果
        """
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            summary_text = request.data.get("summary_text", "").strip()
            
            # 2. 输入校验
            if not file_id:
                return Response(
                    {"status": "failed", "detail": "文件ID不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            if not summary_text:
                return Response(
                    {"status": "failed", "detail": "纪要文本不能为空"},
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
            
            # 4. 检查是否已存在会议纪要
            try:
                summary = MeetingSummary.objects.get(file=file)
                if not summary.summary_text:
                    return Response(
                        {"status": "failed", "detail": "无会议纪要"},
                        status=HTTP_404_NOT_FOUND
                    )
                # 更新会议纪要
                summary.summary_text = summary_text
                summary.is_customized = True
                summary.save()
            except MeetingSummary.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "无会议纪要"},
                    status=HTTP_404_NOT_FOUND
                )
            
            return Response({
                "status": "success",
                "detail": "会议纪要更新成功",
                "file_id": file_id,
                "is_customized": True,
                "updated_at": summary.updated_at.isoformat()
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"纪要更新失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 会议摘要编辑接口（分离） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingAbstractUpdateView(APIView):
    """会议摘要更新视图：编辑已生成的会议摘要"""
    @method_decorator(require_auth)
    def put(self, request):
        """
        更新会议摘要
        
        Args:
            request: HTTP请求对象，包含文件ID和摘要文本
            
        Returns:
            Response: 更新结果
        """
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            abstract_text = request.data.get("abstract_text", "").strip()
            
            # 2. 输入校验
            if not file_id:
                return Response(
                    {"status": "failed", "detail": "文件ID不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            if not abstract_text:
                return Response(
                    {"status": "failed", "detail": "摘要文本不能为空"},
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
            
            # 4. 检查是否已存在会议摘要
            try:
                summary = MeetingSummary.objects.get(file=file)
                if not summary.abstract_text:
                    return Response(
                        {"status": "failed", "detail": "无会议摘要"},
                        status=HTTP_404_NOT_FOUND
                    )
                # 更新会议摘要
                summary.abstract_text = abstract_text
                summary.is_customized = True
                summary.save()
            except MeetingSummary.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "无会议摘要"},
                    status=HTTP_404_NOT_FOUND
                )
            
            return Response({
                "status": "success",
                "detail": "会议摘要更新成功",
                "file_id": file_id,
                "is_customized": True,
                "updated_at": summary.updated_at.isoformat()
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"摘要更新失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 会议分段工具函数 -------------------

# 获取文件的转录文本
def get_transcription(file):
    """
    获取文件的转录文本
    
    Args:
        file: 文件对象
        
    Returns:
        tuple: (转录文本, 错误信息)
    """
    print(f"[DEBUG] 获取文件转录文本 - 文件ID: {file.id}, 文件名: {file.original_name}")
    try:
        transcription = Transcription.objects.get(file=file)
        if not transcription.transcription_text:
            print(f"[DEBUG] 转录文本为空")
            return None, "逐字稿内容为空"
        print(f"[DEBUG] 转录文本长度: {len(transcription.transcription_text)}")
        return transcription.transcription_text, None
    except Transcription.DoesNotExist:
        print(f"[DEBUG] 转录文本不存在")
        return None, "逐字稿不存在"

# 获取音频/视频文件的时长（秒）
def get_audio_duration(file_path):
    """
    获取音频/视频文件的时长（秒）
    
    Args:
        file_path: 文件路径
        
    Returns:
        float: 文件时长（秒）
    """
    print(f"[DEBUG] 获取文件时长 - 文件路径: {file_path}")
    try:
        # 检查文件是否存在
        import os
        if not os.path.exists(file_path):
            print(f"[DEBUG] 文件不存在: {file_path}")
            return 3600
        
        # 使用 ffprobe 命令获取文件信息
        print(f"[DEBUG] 执行 ffprobe 命令")
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path],
            capture_output=True,
            text=True
        )
        
        print(f"[DEBUG] ffprobe 返回码: {result.returncode}")
        if result.stderr:
            print(f"[DEBUG] ffprobe 错误输出: {result.stderr}")
        
        info = json.loads(result.stdout)
        duration = float(info['format']['duration'])
        print(f"[DEBUG] 文件时长: {duration} 秒")
        return duration
    except Exception as e:
        print(f"[DEBUG] 获取文件时长失败: {e}")
        import traceback
        print(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
        return 3600  # 默认值，以防获取失败

# 基于内容语义进行分段
def segment_transcription(transcription_text, total_duration=3600):
    """
    基于内容语义进行分段
    
    Args:
        transcription_text: 转录文本
        total_duration: 总时长（秒）
        
    Returns:
        list: 分段列表
    """
    print(f"[DEBUG] 开始语义分段 - 总时长: {total_duration} 秒")
    import re
    segments = []
    
    # 按句子分割
    sentences = []
    current_sentence = ""
    for char in transcription_text:
        current_sentence += char
        if char in [".", "。", "!", "！", "?", "？"]:
            sentences.append(current_sentence)
            current_sentence = ""
    if current_sentence:
        sentences.append(current_sentence)
    
    # 按说话人分割
    speaker_segments = []
    current_speaker = None
    current_content = []
    current_start = 0.0
    
    for i, sentence in enumerate(sentences):
        # 检测说话人
        speaker_match = re.match(r'(.+?):\s', sentence)
        if speaker_match:
            speaker = speaker_match.group(1)
            if speaker != current_speaker:
                if current_content:
                    # 计算时间范围
                    end_time = (i / len(sentences)) * total_duration
                    content = "".join(current_content)
                    if content.strip():
                        speaker_segments.append({
                            "start_time": current_start,
                            "end_time": end_time,
                            "content": content,
                            "speaker": current_speaker
                        })
                current_speaker = speaker
                current_content = [sentence]
                current_start = (i / len(sentences)) * total_duration
            else:
                current_content.append(sentence)
        else:
            current_content.append(sentence)
    
    # 添加最后一个说话人段落
    if current_content:
        end_time = total_duration
        content = "".join(current_content)
        if content.strip():
            speaker_segments.append({
                "start_time": current_start,
                "end_time": end_time,
                "content": content,
                "speaker": current_speaker
            })
    
    # 合并短段落
    merged_segments = []
    current_segment = None
    
    for segment in speaker_segments:
        if not current_segment:
            current_segment = segment.copy()
        else:
            # 如果当前段落较短，与下一段合并
            if len(current_segment["content"]) < 200:
                current_segment["content"] += segment["content"]
                current_segment["end_time"] = segment["end_time"]
            else:
                merged_segments.append(current_segment)
                current_segment = segment.copy()
    
    if current_segment:
        merged_segments.append(current_segment)
    
    # 处理过长段落
    final_segments = []
    for segment in merged_segments:
        if len(segment["content"]) > 600:
            # 分割过长段落
            content = segment["content"]
            start_time = segment["start_time"]
            end_time = segment["end_time"]
            duration = end_time - start_time
            
            # 按句子分割
            sub_sentences = []
            current_sub_sentence = ""
            for char in content:
                current_sub_sentence += char
                if char in [".", "。", "!", "！", "?", "？"]:
                    sub_sentences.append(current_sub_sentence)
                    current_sub_sentence = ""
            if current_sub_sentence:
                sub_sentences.append(current_sub_sentence)
            
            # 重新分段
            sub_segment_start = start_time
            sub_content = []
            
            for i, sub_sentence in enumerate(sub_sentences):
                sub_content.append(sub_sentence)
                sub_content_str = "".join(sub_content)
                
                if len(sub_content_str) > 400 or i == len(sub_sentences) - 1:
                    sub_segment_end = start_time + (i + 1) / len(sub_sentences) * duration
                    final_segments.append({
                        "start_time": sub_segment_start,
                        "end_time": sub_segment_end,
                        "content": sub_content_str
                    })
                    sub_segment_start = sub_segment_end
                    sub_content = []
        else:
            final_segments.append({
                "start_time": segment["start_time"],
                "end_time": segment["end_time"],
                "content": segment["content"]
            })
    
    print(f"[DEBUG] 语义分段完成，共 {len(final_segments)} 个分段")
    for i, seg in enumerate(final_segments):
        print(f"[DEBUG] 分段 {i+1}: {seg['start_time']}s - {seg['end_time']}s, 内容长度: {len(seg['content'])}")
    return final_segments

# 使用LLM优化分段并生成标题和总结
def optimize_segments_with_llm(segments):
    """
    使用LLM优化分段并生成标题和总结
    
    Args:
        segments: 分段列表
        
    Returns:
        list: 优化后的分段列表
    """
    print(f"[DEBUG] 开始使用单个LLM处理分段，共 {len(segments)} 个")
    optimized_segments = []
    
    for i, segment in enumerate(segments):
        print(f"[DEBUG] 处理分段 {i+1}/{len(segments)}")
        # 准备提示词，明确要求生成总结
        prompt = f"请分析以下会议段落内容，完成以下任务：\n1. 检查段落边界是否合理，如果不合理，请调整\n2. 为段落生成一个简洁的小标题（不超过10字）\n3. 生成段落的核心内容总结，包含两部分：\n   a. 该段落的会议核心内容（核心）\n   b. 该段落中各成员的核心观点（辅助）\nc. 按时间轴梳理关键环节、核心发言与讨论过程\n\n要求：\n- 小标题：不超过10个字\n- 核心内容总结：100-250字\n- 用户名称必须严格按照原文，不能修改。\n\n段落内容：\n{segment['content']}\n\n开始时间：{segment['start_time']}秒\n结束时间：{segment['end_time']}秒\n\n请按照以下JSON格式返回结果：\n{{\n  \"title\": \"小标题\",\n  \"summary\": \"核心内容总结（包含会议核心内容和各成员核心观点）\",\n  \"is_boundary_reasonable\": true/false,\n  \"suggested_start_time\": 0.0,\n  \"suggested_end_time\": 0.0\n}}\n\n重要：\n1. 即使内容较短或质量不高，也必须生成标题和总结，不能为空。\n2. 总结应包含会议核心内容和各成员的核心观点，语言简洁客观、逻辑清晰。\n3. 小标题不超过10字，核心内容总结100-250字。\n4. 用户名称必须严格按照原文，不能修改。"
        
        print(f"[DEBUG] 分段 {i+1} 提示词长度: {len(prompt)}")
        
        # 调用LLM
        try:
            print(f"[DEBUG] 分段 {i+1} 开始调用LLM")
            print(f"[DEBUG] LLM配置 - 模型: {settings.LLM_CONFIG['model_name']}, API密钥: {'*'*10}{settings.LLM_CONFIG['api_key'][-5:] if settings.LLM_CONFIG['api_key'] else '未设置'}")
            
            response = llm_client.chat.completions.create(
                model=settings.LLM_CONFIG["model_name"],
                messages=[
                    {"role": "system", "content": "你是专业的会议分析助手，擅长分析会议内容并生成简洁的标题和总结。即使内容质量不高或较短，也能提取核心信息。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                temperature=0.3,
                max_tokens=500,
                timeout=120  # 增加超时设置
            )
            print(f"[DEBUG] 分段 {i+1} LLM调用成功")
            
            # 解析LLM响应
            try:
                import json
                llm_response = response.choices[0].message.content.strip()
                print(f"[DEBUG] 分段 {i+1} LLM返回内容长度: {len(llm_response)}")
                print(f"[DEBUG] 分段 {i+1} LLM返回内容: {llm_response[:200]}..." if len(llm_response) > 200 else f"[DEBUG] 分段 {i+1} LLM返回内容: {llm_response}")
                
                result = json.loads(llm_response)
                print(f"[DEBUG] 分段 {i+1} 解析成功 - 标题: {result.get('title')}, 摘要: {result.get('summary', '')[:50]}...")
                
                # 确保summary不为空
                if not result.get("summary"):
                    result["summary"] = "该段落主要讨论了相关内容。"
                
                optimized_segment = {
                    "index": i,
                    "start_time": result.get("suggested_start_time", segment["start_time"]),
                    "end_time": result.get("suggested_end_time", segment["end_time"]),
                    "title": result.get("title", f"段落{i+1}"),
                    "content": segment["content"],
                    "summary": result.get("summary", "该段落主要讨论了相关内容。"),
                    "is_edited": False
                }
                optimized_segments.append(optimized_segment)
            except Exception as e:
                print(f"[DEBUG] 分段 {i+1} 解析失败: {e}")
                import traceback
                print(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
                # 如果解析失败，使用默认值，但确保summary不为空
                optimized_segment = {
                    "index": i,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "title": f"段落{i+1}",
                    "content": segment["content"],
                    "summary": "该段落主要讨论了相关内容。",
                    "is_edited": False
                }
                optimized_segments.append(optimized_segment)
        except Exception as e:
            # 如果API调用失败，使用默认值，但确保summary不为空
            print(f"[DEBUG] 分段 {i+1} LLM调用失败: {e}")
            import traceback
            print(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
            optimized_segment = {
                "index": i,
                "start_time": segment["start_time"],
                "end_time": segment["end_time"],
                "title": f"段落{i+1}",
                "content": segment["content"],
                "summary": "该段落主要讨论了相关内容。",
                "is_edited": False
            }
            optimized_segments.append(optimized_segment)
    
    print(f"[DEBUG] 单个LLM处理完成，共 {len(optimized_segments)} 个分段")
    return optimized_segments

# 批量使用LLM优化分段并生成标题和总结
def optimize_segments_with_llm_batch(segments):
    """
    批量使用LLM优化分段并生成标题和总结
    
    Args:
        segments: 分段列表
        
    Returns:
        list: 优化后的分段列表
    """
    print(f"[DEBUG] ========== 开始批量LLM处理 ==========")
    print(f"[DEBUG] 待处理的分段数量: {len(segments)}")
    if not segments:
        print(f"[DEBUG] 没有分段需要处理")
        return []
    
    # 准备批量处理的提示词
    batch_prompt = "请分析以下会议段落内容，为每个段落完成以下任务：\n1. 检查段落边界是否合理\n2. 为段落生成一个简洁的小标题（不超过10字）\n3. 生成段落的核心内容总结，包含两部分：\n   a. 该段落的会议核心内容（核心）\n   b. 该段落中各成员的核心观点（辅助）\nc. 按时间轴梳理关键环节、核心发言与讨论过程\n\n要求：\n- 小标题：不超过10个字\n- 核心内容总结：100-250字\n\n"
    
    for i, segment in enumerate(segments):
        batch_prompt += f"段落 {i+1}：\n内容：{segment['content']}\n开始时间：{segment['start_time']}秒\n结束时间：{segment['end_time']}秒\n\n"
    
    batch_prompt += "请按照以下格式返回每个段落的结果，每个段落一个JSON对象：\n[\n  {\n    \"index\": 0,\n    \"title\": \"小标题\",\n    \"summary\": \"核心内容总结（包含会议核心内容和各成员核心观点）\",\n    \"is_boundary_reasonable\": true,\n    \"suggested_start_time\": 0.0,\n    \"suggested_end_time\": 0.0\n  },\n  ...\n]\n\n重要：\n1. 每个段落都必须生成标题和总结，不能为空。\n2. 总结应包含会议核心内容和各成员的核心观点，语言简洁客观、逻辑清晰。\n3. 小标题不超过10字，核心内容总结100-250字。\n4. 用户名称必须严格按照原文，不能修改。"
    
    print(f"[DEBUG] 批量提示词长度: {len(batch_prompt)}")
    print(f"[DEBUG] LLM配置 - 模型: {settings.LLM_CONFIG['model_name']}, API密钥: {'*'*10}{settings.LLM_CONFIG['api_key'][-5:] if settings.LLM_CONFIG['api_key'] else '未设置'}, Base URL: {settings.LLM_CONFIG.get('base_url', '未设置')}")
    
    try:
        # 调用LLM
        print(f"[DEBUG] ========== 开始调用批量LLM API ==========")
        response = llm_client.chat.completions.create(
            model=settings.LLM_CONFIG["model_name"],
            messages=[
                {"role": "system", "content": "你是专业的会议分析助手，擅长分析会议内容并生成简洁的标题和总结。即使内容质量不高或较短，也能提取核心信息。"},
                {"role": "user", "content": batch_prompt}
            ],
            stream=False,
            temperature=0.3,
            max_tokens=4000,
            timeout=300
        )
        print(f"[DEBUG] ========== 批量LLM API调用成功 ==========")
        
        # 解析响应
        try:
            import json
            llm_response = response.choices[0].message.content.strip()
            print(f"[DEBUG] LLM返回内容长度: {len(llm_response)}")
            print(f"[DEBUG] LLM返回内容: {llm_response[:500]}..." if len(llm_response) > 500 else f"[DEBUG] LLM返回内容: {llm_response}")
            
            results = json.loads(llm_response)
            print(f"[DEBUG] 解析到 {len(results)} 个结果")
            
            optimized_segments = []
            
            for i, result in enumerate(results):
                if i < len(segments):
                    print(f"[DEBUG] 处理结果 {i+1} - 标题: {result.get('title')}, 摘要: {result.get('summary', '')[:50]}...")
                    optimized_segment = {
                        "index": i,
                        "start_time": result.get("suggested_start_time", segments[i]["start_time"]),
                        "end_time": result.get("suggested_end_time", segments[i]["end_time"]),
                        "title": result.get("title", f"段落{i+1}"),
                        "content": segments[i]["content"],
                        "summary": result.get("summary", "该段落主要讨论了相关内容。"),
                        "is_edited": False
                    }
                    optimized_segments.append(optimized_segment)
            print(f"[DEBUG] ========== 批量LLM处理成功，共 {len(optimized_segments)} 个分段 ==========")
            return optimized_segments
        except Exception as e:
            print(f"[DEBUG] ========== 解析LLM响应失败 ==========")
            print(f"[DEBUG] 错误信息: {e}")
            import traceback
            print(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
            # 解析失败时，为每个分段生成默认值
            print(f"[DEBUG] 使用默认值代替")
            optimized_segments = []
            for i, segment in enumerate(segments):
                optimized_segment = {
                    "index": i,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "title": f"段落{i+1}",
                    "content": segment["content"],
                    "summary": "该段落主要讨论了相关内容。",
                    "is_edited": False
                }
                optimized_segments.append(optimized_segment)
            return optimized_segments
    except Exception as e:
        print(f"[DEBUG] ========== LLM批量调用失败 ==========")
        print(f"[DEBUG] 错误信息: {e}")
        import traceback
        print(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
        # 批量处理失败时，回退到逐个处理
        print(f"[DEBUG] ========== 回退到逐个处理 ==========")
        return optimize_segments_with_llm(segments)

# 存储分段数据到数据库
def store_segments(file, user, segments):
    """
    存储分段数据到数据库
    
    Args:
        file: 文件对象
        user: 用户对象
        segments: 分段列表
    """
    print(f"[DEBUG] ========== 开始存储分段数据 ==========")
    print(f"[DEBUG] 文件ID: {file.id}, 用户ID: {user.id}, 待存储分段数: {len(segments)}")
    
    # 先删除已存在的分段
    print(f"[DEBUG] 删除旧分段数据")
    MeetingSegment.objects.filter(file=file).delete()
    
    # 保存新的分段
    print(f"[DEBUG] 开始保存新分段")
    for i, segment in enumerate(segments):
        print(f"[DEBUG] 保存分段 {i+1}/{len(segments)} - 标题: {segment['title']}")
        MeetingSegment.objects.create(
            file=file,
            user=user,
            segment_index=i,
            start_time=segment["start_time"],
            end_time=segment["end_time"],
            title=segment["title"],
            content=segment["content"],
            summary=segment["summary"],
            is_edited=segment.get("is_edited", False)
        )
    print(f"[DEBUG] ========== 分段数据存储完成 ==========")

# 序列化分段数据
def serialize_segments(segments):
    """
    序列化分段数据
    
    Args:
        segments: 分段对象列表
        
    Returns:
        list: 序列化后的分段数据列表
    """
    return [
        {
            "id": segment.id,
            "index": segment.segment_index,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "title": segment.title,
            "summary": segment.summary,
            "is_edited": segment.is_edited,
            "created_at": segment.created_at.isoformat(),
            "updated_at": segment.updated_at.isoformat()
        } for segment in segments
    ]

# ------------------- 生成分段接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class GenerateSegmentsView(APIView):
    """生成分段视图：基于转录文本生成语义分段"""
    @method_decorator(require_auth)
    def post(self, request):
        """
        生成会议文件分段
        
        Args:
            request: HTTP请求对象，包含文件ID、强制更新参数
            
        Returns:
            Response: 包含分段数据的响应
        """
        print(f"[DEBUG] ========== 开始生成分段 ==========")
        print(f"[DEBUG] 请求参数: {request.data}")
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            force_update = request.data.get("force_update", False)
            print(f"[DEBUG] 文件ID: {file_id}, 强制更新: {force_update}")
            
            # 2. 输入校验
            if not file_id:
                print(f"[DEBUG] 文件ID为空")
                return Response(
                    {"status": "failed", "detail": "文件ID不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 3. 检查文件是否存在且属于当前用户
            try:
                print(f"[DEBUG] 查询文件信息")
                file = UploadedFile.objects.get(id=file_id, user=request.user)
                print(f"[DEBUG] 文件信息 - 原始名称: {file.original_name}, 存储名称: {file.stored_name}, 文件类型: {file.file_type}")
            except UploadedFile.DoesNotExist:
                print(f"[DEBUG] 文件不存在或无权限")
                return Response(
                    {"status": "failed", "detail": "文件不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 4. 检查是否已存在分段数据
            existing_segments = MeetingSegment.objects.filter(file=file)
            if existing_segments.exists() and not force_update:
                print(f"[DEBUG] 分段数据已存在，直接返回")
                return Response({
                    "status": "success",
                    "detail": "分段数据已存在",
                    "segments": serialize_segments(existing_segments),
                    "total_segments": existing_segments.count(),
                    "generated_at": existing_segments.first().created_at.isoformat()
                }, status=HTTP_200_OK)
            
            print(f"[DEBUG] 开始生成分段 - 是否强制更新: {force_update}")
            
            # 5. 获取转录文本
            transcription_text, error = get_transcription(file)
            if not transcription_text:
                print(f"[DEBUG] 获取转录文本失败: {error}")
                return Response(
                    {"status": "failed", "detail": error},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 6. 获取文件实际时长
            file_path = os.path.join(settings.FILE_UPLOAD_DIR, file.stored_name)
            print(f"[DEBUG] 文件完整路径: {file_path}")
            total_duration = get_audio_duration(file_path)
            
            # 7. 初步分段（双模式：语义聚类 / 规则分段，默认语义）
            segment_mode = request.data.get("mode", "semantic")  # "semantic" 或 "rule_based"
            print(f"[DEBUG] 分段模式: {segment_mode}")
            if segment_mode == "semantic":
                print(f"[DEBUG] 使用语义聚类分段（KMeans + Embedding）")
                initial_segments = semantic_segment_transcription(
                    transcription_text, total_duration=total_duration
                )
            else:
                print(f"[DEBUG] 使用规则分段（说话人+长度）")
                initial_segments = segment_transcription(
                    transcription_text, total_duration=total_duration
                )
            
            # 8. LLM优化（使用批量处理）
            print(f"[DEBUG] 开始LLM优化")
            optimized_segments = optimize_segments_with_llm_batch(initial_segments)
            
            # 8. 存储分段数据
            store_segments(file, request.user, optimized_segments)
            
            # 9. 获取存储后的分段数据
            print(f"[DEBUG] 查询存储后的分段数据")
            stored_segments = MeetingSegment.objects.filter(file=file)
            print(f"[DEBUG] 共存储 {stored_segments.count()} 个分段")
            
            print(f"[DEBUG] ========== 分段生成完成 ==========")
            return Response({
                "status": "success",
                "detail": "分段生成成功",
                "segments": serialize_segments(stored_segments),
                "total_segments": stored_segments.count(),
                "generated_at": stored_segments.first().created_at.isoformat()
            }, status=HTTP_200_OK)
        except Exception as e:
            print(f"[DEBUG] ========== 分段生成失败 ==========")
            print(f"[DEBUG] 错误信息: {e}")
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"生成分段失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 获取分段列表接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SegmentsListView(APIView):
    @method_decorator(require_auth)
    def get(self, request):
        """获取会议文件分段列表"""
        try:
            # 1. 提取请求参数
            file_id = request.query_params.get("file_id")
            
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
            
            # 4. 获取分段数据
            segments = MeetingSegment.objects.filter(file=file).order_by("segment_index")
            
            if not segments.exists():
                return Response(
                    {"status": "failed", "detail": "分段数据不存在"},
                    status=HTTP_404_NOT_FOUND
                )
            
            return Response({
                "status": "success",
                "segments": serialize_segments(segments),
                "total_segments": segments.count(),
                "generated_at": segments.first().created_at.isoformat()
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"获取分段失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )

# ------------------- 编辑分段接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class SegmentUpdateView(APIView):
    @method_decorator(require_auth)
    def put(self, request, segment_id):
        """编辑会议分段"""
        try:
            # 1. 提取请求参数
            title = request.data.get("title", "").strip()
            summary = request.data.get("summary", "").strip()
            start_time = request.data.get("start_time")
            end_time = request.data.get("end_time")
            
            # 2. 输入校验
            if not title:
                return Response(
                    {"status": "failed", "detail": "小标题不能为空"},
                    status=HTTP_400_BAD_REQUEST
                )
            
            # 时间戳校验
            if start_time is not None or end_time is not None:
                try:
                    if start_time is not None:
                        start_time = float(start_time)
                    if end_time is not None:
                        end_time = float(end_time)
                    if start_time is not None and end_time is not None and start_time >= end_time:
                        return Response(
                            {"status": "failed", "detail": "开始时间必须小于结束时间"},
                            status=HTTP_400_BAD_REQUEST
                        )
                except (ValueError, TypeError):
                    return Response(
                        {"status": "failed", "detail": "时间戳必须是有效的数字"},
                        status=HTTP_400_BAD_REQUEST
                    )
            
            # 3. 检查分段是否存在且属于当前用户
            try:
                segment = MeetingSegment.objects.get(id=segment_id)
                # 验证文件权限
                if segment.file.user != request.user:
                    return Response(
                        {"status": "failed", "detail": "分段不存在或无权限"},
                        status=HTTP_404_NOT_FOUND
                    )
                
                # 获取文件时长
                file = segment.file
                # 尝试从file对象获取duration，如果没有则计算
                file_duration = getattr(file, 'duration', 0)
                if file_duration <= 0:
                    # 如果没有duration字段或值为0，尝试计算文件时长
                    import os
                    file_path = os.path.join(settings.FILE_UPLOAD_DIR, file.stored_name)
                    file_duration = get_audio_duration(file_path)
            except MeetingSegment.DoesNotExist:
                return Response(
                    {"status": "failed", "detail": "分段不存在或无权限"},
                    status=HTTP_404_NOT_FOUND
                )
            
            # 4. 时间戳范围校验
            if start_time is not None or end_time is not None:
                if start_time is not None and (start_time < 0 or start_time > file_duration):
                    return Response(
                        {"status": "failed", "detail": f"开始时间必须在0到{file_duration}秒之间"},
                        status=HTTP_400_BAD_REQUEST
                    )
                if end_time is not None and (end_time < 0 or end_time > file_duration):
                    return Response(
                        {"status": "failed", "detail": f"结束时间必须在0到{file_duration}秒之间"},
                        status=HTTP_400_BAD_REQUEST
                    )
            
            # 5. 更新分段（不更新content）
            segment.title = title
            segment.summary = summary
            if start_time is not None:
                segment.start_time = start_time
            if end_time is not None:
                segment.end_time = end_time
            segment.is_edited = True
            segment.save()
            
            return Response({
                "status": "success",
                "detail": "分段更新成功",
                "segment": {
                    "id": segment.id,
                    "index": segment.segment_index,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "title": segment.title,
                    "summary": segment.summary,
                    "is_edited": segment.is_edited,
                    "updated_at": segment.updated_at.isoformat()
                }
            }, status=HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"更新分段失败：{str(e)}"},
                status=HTTP_400_BAD_REQUEST
            )