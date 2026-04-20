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
from ..models import UploadedFile, MeetingSummary, Transcription
from ..auth_utils import require_auth

# 初始化LLM客户端
llm_client = OpenAI(
    api_key=settings.LLM_CONFIG["api_key"],
    base_url=settings.LLM_CONFIG["base_url"]
)

# ------------------- 会议纪要生成接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingSummaryView(APIView):
    @method_decorator(require_auth)
    def post(self, request):
        """基于文件ID生成结构化会议纪要"""
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            output_format = request.data.get("output_format", "txt")
            custom_system_prompt = request.data.get("custom_system_prompt", None)
            custom_user_prompt = request.data.get("custom_user_prompt", None)
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
                        "meeting_minutes": existing_summary.summary_text,
                        "is_customized": existing_summary.is_customized,
                        "timestamp": existing_summary.updated_at.strftime("%Y%m%d_%H%M%S")
                    }, status=HTTP_200_OK)
                except MeetingSummary.DoesNotExist:
                    pass
            
            # 5. 定义默认Prompt
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
            
            # 6. 优先级：自定义 > 默认
            final_system_prompt = custom_system_prompt if (custom_system_prompt and custom_system_prompt.strip()) else default_system_prompt
            final_user_prompt = custom_user_prompt if (custom_user_prompt and custom_user_prompt.strip()) else default_user_prompt
            
            # 7. 调用LLM
            response = llm_client.chat.completions.create(
                model=settings.LLM_CONFIG["model_name"],
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": final_user_prompt}
                ],
                stream=False,
                temperature=0.3,
                max_tokens=4000
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
    @method_decorator(require_auth)
    def post(self, request):
        """基于文件ID生成轻量化会议摘要（核心要点提炼）"""
        try:
            # 1. 提取请求参数
            file_id = request.data.get("file_id")
            abstract_length = request.data.get("abstract_length", "medium")  # short/medium/long
            custom_system_prompt = request.data.get("custom_system_prompt", None)
            custom_user_prompt = request.data.get("custom_user_prompt", None)
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
            
            # 5. 定义默认Prompt（轻量化摘要）
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
            
            # 6. 优先级：自定义 > 默认
            final_system_prompt = custom_system_prompt if (custom_system_prompt and custom_system_prompt.strip()) else default_system_prompt
            final_user_prompt = custom_user_prompt if (custom_user_prompt and custom_user_prompt.strip()) else default_user_prompt
            
            # 7. 调用LLM生成摘要
            response = llm_client.chat.completions.create(
                model=settings.LLM_CONFIG["model_name"],
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": final_user_prompt}
                ],
                stream=False,
                temperature=0.2,  # 更低的温度保证摘要的准确性
                max_tokens=1000
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
                    pass
            
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



# ------------------- 会议纪要编辑接口（分离） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingSummaryUpdateView(APIView):
    @method_decorator(require_auth)
    def put(self, request):
        """更新会议纪要"""
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
    @method_decorator(require_auth)
    def put(self, request):
        """更新会议摘要"""
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