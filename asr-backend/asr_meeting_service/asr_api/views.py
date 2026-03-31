from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from openai import OpenAI
from docx import Document as DocxDocument
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import os
import time
import uuid
from datetime import datetime
import traceback
from .utils import extract_audio_from_video

# ------------------- 视频上传+语音转写 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class VideoASRTranscribeView(APIView):
    def post(self, request):
        """
        视频上传接口：提取音频→ASR转写
        返回：转写文本
        """
        temp_video = None
        temp_audio = None
        try:
            # 1. 校验文件是否上传
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传视频文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            # 2. 校验视频格式
            if not file.name.lower().endswith(settings.ALLOWED_VIDEO_EXTENSIONS):
                return Response(
                    {"status": "failed", "detail": f"仅支持以下视频格式：{settings.ALLOWED_VIDEO_EXTENSIONS}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 保存临时视频文件
            video_filename = f"temp_video_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}_{file.name}"
            temp_video = os.path.join(settings.TEMP_DIR, video_filename)
            with open(temp_video, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # 4. 提取音频（WAV格式）
            audio_filename = f"temp_audio_{uuid.uuid4()}.wav"
            temp_audio = os.path.join(settings.TEMP_DIR, audio_filename)
            if not extract_audio_from_video(temp_video, temp_audio):
                return Response(
                    {"status": "failed", "detail": "视频音频提取失败"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 5. 解析请求参数（同音频接口）
            batch_size_s = request.POST.get("batch_size_s", "")
            # 空值/非数字容错：转为整数，失败则用默认值300
            try:
                batch_size_s = int(batch_size_s.strip()) if batch_size_s.strip() else 300
            except (ValueError, TypeError):
                batch_size_s = 300
            hotword = request.POST.get("hotword", None)
            
            # 6. 调用ASR模型处理提取的音频（增加异常捕获+降级）
            from .models import asr_model
            print(f"{datetime.now()} - 开始处理视频音频: {file.name}")
            try:
                result = asr_model.generate(
                    input=temp_audio,
                    batch_size_s=batch_size_s,
                    hotword=hotword,
                    punc=True,
                    spk_segment=True,  # 说话人识别（易触发异常）
                    merge_vad=True,
                    max_single_segment_time=30
                )
            except IndexError as e:
                # 说话人识别失败，降级为仅转写（关闭spk_segment）
                print(f"{datetime.now()} - 说话人识别失败，降级为纯文本转写：{str(e)}")
                result = asr_model.generate(
                    input=temp_audio,
                    batch_size_s=batch_size_s,
                    hotword=hotword,
                    punc=True,
                    spk_segment=False,  # 关闭说话人识别
                    merge_vad=True,
                    max_single_segment_time=30
                )
            except Exception as e:
                # 其他ASR模型异常
                print(f"{datetime.now()} - ASR模型调用失败：{str(e)}")
                return Response(
                    {"status": "failed", "detail": f"ASR模型处理失败：{str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 7. 格式化转写结果（带时间戳）
            formatted_result = []
            if result and len(result) > 0:
                sentence_info = result[0].get("sentence_info", [])
                if sentence_info:
                    for segment in sentence_info:
                        formatted_result.append({
                            "spk": segment.get("spk", "未知说话人"),
                            "text": segment.get("text", "").strip(),
                            "start_time": round(segment.get("start", 0) / 1000, 2),
                            "end_time": round(segment.get("end", 0) / 1000, 2)
                        })
                elif "value" in result[0]:
                    for segment in result[0]["value"]:
                        formatted_result.append({
                            "spk": segment.get("spk", "未知说话人"),
                            "text": segment.get("text", "").strip(),
                            "start_time": round(segment.get("start", 0) / 1000, 2),
                            "end_time": round(segment.get("end", 0) / 1000, 2)
                        })
            
            if not formatted_result:
                formatted_result = [{
                    "spk": "未知说话人",
                    "text": "未识别到有效语音内容",
                    "start_time": 0.00,
                    "end_time": 0.00
                }]
            
            # 10. 返回结果
            return Response({
                "status": "success",
                "filename": file.name,
                "transcription": formatted_result,
                "note": "已完成视频音频提取+ASR转写",
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"视频处理失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # 清理临时文件
            for temp_file in [temp_video, temp_audio]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"{datetime.now()} - 临时文件 {temp_file} 已删除")
                    except Exception as e:
                        print(f"{datetime.now()} - 临时文件删除失败：{str(e)}")

# 初始化LLM客户端
llm_client = OpenAI(
    api_key=settings.LLM_CONFIG["api_key"],
    base_url=settings.LLM_CONFIG["base_url"]
)

# ------------------- 基础接口（健康检查） -------------------
class HealthCheckView(APIView):
    def get(self, request):
        """服务健康检查，对齐FastAPI的/接口"""
        return Response({
            "status": "healthy",
            "service": "ASR会议纪要服务",
            "timestamp": datetime.now().isoformat(),
            "features": ["语音转文字（带标点/说话人）", "会议纪要生成", "Word文档导出"]
        })

# ------------------- ASR语音转文字接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class ASRTranscribeView(APIView):
    def post(self, request):
        """语音转文字接口，支持多格式音频、标点恢复、说话人识别 + 时间戳返回"""
        temp_file = None
        try:
            # 1. 校验文件是否上传
            if 'file' not in request.FILES:
                return Response(
                    {"status": "failed", "detail": "未上传音频文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            # 2. 校验文件格式
            if not file.name.lower().endswith(settings.ALLOWED_EXTENSIONS):
                return Response(
                    {"status": "failed", "detail": f"仅支持以下音频格式：{settings.ALLOWED_EXTENSIONS}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 保存临时文件
            temp_filename = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}_{file.name}"
            temp_file = os.path.join(settings.TEMP_DIR, temp_filename)
            with open(temp_file, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # 4. 解析请求参数
            batch_size_s = int(request.POST.get("batch_size_s", 300))
            hotword = request.POST.get("hotword", None)
            
            # 5. 调用ASR模型（增加异常捕获+降级）
            from .models import asr_model
            print(f"{datetime.now()} - 开始处理音频文件: {file.name}")
            try:
                result = asr_model.generate(
                    input=temp_file,
                    batch_size_s=batch_size_s,
                    hotword=hotword,
                    punc=True,
                    spk_segment=True,
                    merge_vad=True,
                    max_single_segment_time=30
                )
            except IndexError as e:
                # 说话人识别失败，降级为纯文本转写
                print(f"{datetime.now()} - 说话人识别失败，降级为纯文本转写：{str(e)}")
                result = asr_model.generate(
                    input=temp_file,
                    batch_size_s=batch_size_s,
                    hotword=hotword,
                    punc=True,
                    spk_segment=False,  # 关闭说话人识别
                    merge_vad=True,
                    max_single_segment_time=30
                )
            except Exception as e:
                print(f"{datetime.now()} - ASR模型调用失败：{str(e)}")
                return Response(
                    {"status": "failed", "detail": f"ASR模型处理失败：{str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 6. 格式化结果（新增 start_time + end_time）
            formatted_result = []
            if result and len(result) > 0:
                sentence_info = result[0].get("sentence_info", [])
                if sentence_info:
                    for segment in sentence_info:
                        formatted_result.append({
                            "spk": segment.get("spk", "未知说话人"),
                            "text": segment.get("text", "").strip(),
                            "start_time": round(segment.get("start", 0) / 1000, 2),  # 毫秒 → 秒
                            "end_time": round(segment.get("end", 0) / 1000, 2)
                        })
                elif "value" in result[0]:
                    for segment in result[0]["value"]:
                        formatted_result.append({
                            "spk": segment.get("spk", "未知说话人"),
                            "text": segment.get("text", "").strip(),
                            "start_time": round(segment.get("start", 0) / 1000, 2),
                            "end_time": round(segment.get("end", 0) / 1000, 2)
                        })
            
            if not formatted_result:
                formatted_result = [{
                    "spk": "未知说话人",
                    "text": "未识别到有效语音内容",
                    "start_time": 0.00,
                    "end_time": 0.00
                }]
            
            # 7. 返回结果（带时间戳）
            return Response({
                "status": "success",
                "filename": file.name,
                "transcription": formatted_result,
                "note": "已启用标点恢复+说话人识别+时间戳（CPU模式）",
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"音频处理失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"{datetime.now()} - 临时文件 {temp_file} 已删除")
                except Exception as e:
                    print(f"{datetime.now()} - 临时文件删除失败：{str(e)}")

# ------------------- 会议纪要生成接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingSummaryView(APIView):
    def post(self, request):
        """基于转录文本生成结构化会议纪要"""
        try:
            # 1. 提取请求参数
            transcription_text = request.data.get("transcription_text", "").strip()
            output_format = request.data.get("output_format", "txt")
            custom_system_prompt = request.data.get("custom_system_prompt", None)
            custom_user_prompt = request.data.get("custom_user_prompt", None)
            
            # 2. 输入校验
            if not transcription_text:
                return Response(
                    {"status": "failed", "detail": "转录文本不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 定义默认Prompt
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
            
            # 4. 优先级：自定义 > 默认
            final_system_prompt = custom_system_prompt if (custom_system_prompt and custom_system_prompt.strip()) else default_system_prompt
            final_user_prompt = custom_user_prompt if (custom_user_prompt and custom_user_prompt.strip()) else default_user_prompt
            
            # 5. 调用LLM
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
            
            # 6. 提取结果
            meeting_minutes = response.choices[0].message.content.strip()
            
            return Response({
                "status": "success",
                "meeting_minutes": meeting_minutes,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "output_format": output_format,
                "used_system_prompt": final_system_prompt,
                "used_user_prompt": final_user_prompt
            })
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"纪要生成失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- 会议摘要生成接口（轻量化） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeetingAbstractView(APIView):
    def post(self, request):
        """基于转录文本生成轻量化会议摘要（核心要点提炼）"""
        try:
            # 1. 提取请求参数
            transcription_text = request.data.get("transcription_text", "").strip()
            abstract_length = request.data.get("abstract_length", "medium")  # short/medium/long
            custom_system_prompt = request.data.get("custom_system_prompt", None)
            custom_user_prompt = request.data.get("custom_user_prompt", None)
            
            # 2. 输入校验
            if not transcription_text:
                return Response(
                    {"status": "failed", "detail": "转录文本不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 定义长度对应的字数限制
            length_config = {
                "short": "100-200字",
                "medium": "200-400字",
                "long": "400-600字"
            }
            target_length = length_config.get(abstract_length, "200-400字")
            
            # 4. 定义默认Prompt（轻量化摘要）
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
            
            # 5. 优先级：自定义 > 默认
            final_system_prompt = custom_system_prompt if (custom_system_prompt and custom_system_prompt.strip()) else default_system_prompt
            final_user_prompt = custom_user_prompt if (custom_user_prompt and custom_user_prompt.strip()) else default_user_prompt
            
            # 6. 调用LLM生成摘要
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
            
            # 7. 提取结果
            meeting_abstract = response.choices[0].message.content.strip()
            
            return Response({
                "status": "success",
                "meeting_abstract": meeting_abstract,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "abstract_length": abstract_length,
                "target_word_count": target_length,
                "used_system_prompt": final_system_prompt,
                "used_user_prompt": final_user_prompt
            })
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"摘要生成失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Word导出接口（转录文本） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class ExportTranscriptionWordView(APIView):
    def post(self, request):
        """导出语音分离结果为Word文档"""
        try:
            # 1. 提取参数
            transcription_text = request.data.get("transcription_text", "").strip()
            file_name = request.data.get("file_name", "会议记录")
            
            # 2. 输入校验
            if not transcription_text:
                return Response(
                    {"status": "failed", "detail": "语音分离文本不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 生成唯一文件名
            file_uuid = str(uuid.uuid4())
            doc_path = os.path.join(settings.TEMP_DIR, f"{file_name}_语音分离_{file_uuid}.docx")
            
            # 4. 创建Word文档
            doc = DocxDocument()
            
            # 标题
            title_para = doc.add_heading(level=0)
            title_run = title_para.add_run(f"{file_name} - 语音分离结果")
            title_run.font.size = Pt(20)
            title_run.bold = True
            title_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # 生成时间
            time_para = doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            time_para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
            time_para.add_run("\n\n")
            
            # 内容
            content_para = doc.add_paragraph()
            content_run = content_para.add_run(transcription_text)
            content_run.font.size = Pt(12)
            content_run.font.name = "微软雅黑"
            content_para.line_spacing = 1.5
            
            # 保存文档
            doc.save(doc_path)
            
            # 5. 返回文件下载
            response = FileResponse(
                open(doc_path, 'rb'),
                filename=f"{file_name}_语音分离结果.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            # 注：生产环境需添加文件清理逻辑（如定时任务）
            return response
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"生成语音分离Word失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Word导出接口（会议纪要） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class ExportSummaryWordView(APIView):
    def post(self, request):
        """导出会议纪要为Word文档"""
        try:
            # 1. 提取参数
            summary_text = request.data.get("summary_text", "").strip()
            file_name = request.data.get("file_name", "会议记录")
            
            # 2. 输入校验
            if not summary_text:
                return Response(
                    {"status": "failed", "detail": "会议纪要文本不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 生成唯一文件名
            file_uuid = str(uuid.uuid4())
            doc_path = os.path.join(settings.TEMP_DIR, f"{file_name}_会议纪要_{file_uuid}.docx")
            
            # 4. 创建Word文档
            doc = DocxDocument()
            
            # 标题
            title_para = doc.add_heading(level=0)
            title_run = title_para.add_run(f"{file_name} - 会议纪要")
            title_run.font.size = Pt(20)
            title_run.bold = True
            title_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # 生成时间
            time_para = doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            time_para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
            time_para.add_run("\n\n")
            
            # 内容
            content_para = doc.add_paragraph()
            content_run = content_para.add_run(summary_text)
            content_run.font.size = Pt(12)
            content_run.font.name = "微软雅黑"
            content_para.line_spacing = 1.5
            
            # 保存文档
            doc.save(doc_path)
            
            # 5. 返回文件下载
            response = FileResponse(
                open(doc_path, 'rb'),
                filename=f"{file_name}_会议纪要.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            return response
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"生成会议纪要Word失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------- Word导出接口（会议摘要） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class ExportAbstractWordView(APIView):
    def post(self, request):
        """导出会议摘要为Word文档"""
        try:
            # 1. 提取参数
            abstract_text = request.data.get("abstract_text", "").strip()
            file_name = request.data.get("file_name", "会议记录")
            
            # 2. 输入校验
            if not abstract_text:
                return Response(
                    {"status": "failed", "detail": "会议摘要文本不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. 生成唯一文件名
            file_uuid = str(uuid.uuid4())
            doc_path = os.path.join(settings.TEMP_DIR, f"{file_name}_会议摘要_{file_uuid}.docx")
            
            # 4. 创建Word文档
            doc = DocxDocument()
            
            # 标题
            title_para = doc.add_heading(level=0)
            title_run = title_para.add_run(f"{file_name} - 会议摘要")
            title_run.font.size = Pt(20)
            title_run.bold = True
            title_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # 生成时间
            time_para = doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            time_para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
            time_para.add_run("\n\n")
            
            # 摘要内容（特殊格式优化）
            abstract_para = doc.add_paragraph()
            abstract_run = abstract_para.add_run("【核心摘要】\n")
            abstract_run.bold = True
            abstract_run.font.size = Pt(14)
            
            content_run = abstract_para.add_run(abstract_text)
            content_run.font.size = Pt(12)
            content_run.font.name = "微软雅黑"
            abstract_para.line_spacing = 1.5
            
            # 保存文档
            doc.save(doc_path)
            
            # 5. 返回文件下载
            response = FileResponse(
                open(doc_path, 'rb'),
                filename=f"{file_name}_会议摘要.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            return response
        
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"status": "failed", "detail": f"生成会议摘要Word失败：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )