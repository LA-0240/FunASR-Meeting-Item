# ==========================================
# RAG API - 智能会议助手接口
# ==========================================
import threading
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asr_api.models import UploadedFile
from asr_api.auth_utils import require_auth
from asr_api.rag import (
    MeetingAgent,
    Indexer,
    VectorStore,
    Retriever
)
from asr_api.indexer_manager import IndexerManager
import logging

logger = logging.getLogger(__name__)


# 异步索引任务
def _index_task(file_id):
    """后台索引任务"""
    try:
        logger.info(f"📚 [Async] 开始异步索引文件{file_id}...")
        
        # 执行索引
        chunk_count = Indexer.index_file(file_id, rebuild=True)
        
        # 更新状态为完成
        IndexerManager.finish_indexing(file_id, success=True)
        
        logger.info(f"✅ [Async] 文件{file_id}异步索引完成: {chunk_count}块")
        
    except Exception as e:
        logger.error(f"❌ [Async] 文件{file_id}异步索引错误: {e}")
        IndexerManager.finish_indexing(file_id, success=False, error_msg=str(e))


# ------------------- 聊天接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class ChatView(APIView):
    """智能会议助手聊天接口"""

    @method_decorator(require_auth)
    def post(self, request):
        """
        发送聊天消息

        请求参数：
        {
            "file_id": 3,  # 可选，指定会议文件
            "message": "这次会议的主要决定是什么？",
            "session_id": "session_123"  # 可选，会话标识
        }

        返回结果：
        {
            "answer": "...",
            "sources": [...],
            "thinking": "..."
        }
        """
        try:
            user = request.user
            data = request.data

            # 打印调试信息
            print("=" * 80)
            print("📩 [DEBUG] ChatView 收到请求")
            print("📦 [DEBUG] request.data:", data)
            print("📦 [DEBUG] type(data):", type(data))
            print("👤 [DEBUG] user:", user.id if user else None)
            
            # 获取参数
            file_id = data.get("file_id")
            user_message = data.get("message", "").strip()
            session_id = data.get("session_id", f"user_{user.id}")
            
            print(f"📝 [DEBUG] file_id: {file_id}")
            print(f"📝 [DEBUG] user_message: '{user_message}'")
            print("=" * 80)

            # 验证参数
            if not user_message:
                print("❌ [DEBUG] 消息为空！")
                return Response({
                    "status": "failed",
                    "detail": "消息不能为空"
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证文件权限（如果指定了file_id）
            if file_id:
                try:
                    uploaded_file = UploadedFile.objects.get(id=file_id)
                    if uploaded_file.user.id != user.id:
                        return Response({
                            "status": "failed",
                            "detail": "无权访问该文件"
                        }, status=status.HTTP_403_FORBIDDEN)
                except UploadedFile.DoesNotExist:
                    return Response({
                        "status": "failed",
                        "detail": "文件不存在"
                    }, status=status.HTTP_404_NOT_FOUND)

            logger.info(f"🤖 用户{user.id}发送消息: {user_message[:50]}...")

            # 创建Agent
            agent = MeetingAgent(user_id=user.id, file_id=file_id)

            # 这里可以加上会话历史管理（暂时简化）
            # 实际项目可以用数据库或缓存保存会话

            # 发送消息
            result = agent.chat(user_message)

            logger.info(f"✅ Agent回复完成")

            return Response({
                "status": "success",
                "answer": result["answer"],
                "sources": result["sources"],
                "thinking": result["thinking"]
            })

        except Exception as e:
            logger.error(f"❌ 聊天接口错误: {e}")
            return Response({
                "status": "failed",
                "detail": f"服务器错误: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------- 索引接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class IndexFileView(APIView):
    """索引会议文件到向量数据库"""

    @method_decorator(require_auth)
    def post(self, request):
        """
        索引文件（支持异步）

        请求参数：
        {
            "file_id": 3,
            "async": true  # 可选，是否异步执行，默认为true
        }
        """
        try:
            user = request.user
            data = request.data
            file_id = data.get("file_id")
            async_exec = data.get("async", True)  # 默认异步

            if not file_id:
                return Response({
                    "status": "failed",
                    "detail": "file_id不能为空"
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证文件权限
            try:
                uploaded_file = UploadedFile.objects.get(id=file_id)
                if uploaded_file.user.id != user.id:
                    return Response({
                        "status": "failed",
                        "detail": "无权访问该文件"
                    }, status=status.HTTP_403_FORBIDDEN)
            except UploadedFile.DoesNotExist:
                return Response({
                    "status": "failed",
                    "detail": "文件不存在"
                }, status=status.HTTP_404_NOT_FOUND)

            # 检查是否正在索引中
            if IndexerManager.is_indexing(file_id):
                logger.warning(f"文件{file_id}正在索引中，跳过重复请求")
                status_info = IndexerManager.get_status(file_id)
                return Response({
                    "status": "success",
                    "detail": "文件正在索引中",
                    "file_id": file_id,
                    "index_status": status_info
                })

            logger.info(f"📚 请求索引文件{file_id} (async={async_exec})...")

            if async_exec:
                # 异步索引：立即返回，后台处理
                if IndexerManager.start_indexing(file_id):
                    # 启动后台线程
                    thread = threading.Thread(target=_index_task, args=(file_id,), daemon=True)
                    thread.start()
                    
                    logger.info(f"🚀 文件{file_id}异步索引已启动")
                    
                    status_info = IndexerManager.get_status(file_id)
                    return Response({
                        "status": "success",
                        "detail": "异步索引已启动",
                        "file_id": file_id,
                        "index_status": status_info
                    })
                else:
                    # 不应该走到这里（前面已经检查过）
                    status_info = IndexerManager.get_status(file_id)
                    return Response({
                        "status": "success",
                        "detail": "文件正在索引中",
                        "file_id": file_id,
                        "index_status": status_info
                    })
            else:
                # 同步索引（旧行为）
                logger.info(f"📚 开始同步索引文件{file_id}...")
                chunk_count = Indexer.index_file(file_id, rebuild=True)
                logger.info(f"✅ 文件{file_id}同步索引完成: {chunk_count}块")
                
                return Response({
                    "status": "success",
                    "file_id": file_id,
                    "chunk_count": chunk_count
                })

        except Exception as e:
            logger.error(f"❌ 索引接口错误: {e}")
            return Response({
                "status": "failed",
                "detail": f"服务器错误: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------- 索引状态接口 -------------------
@method_decorator(csrf_exempt, name='dispatch')
class IndexStatusView(APIView):
    """获取索引状态（包括异步索引进度）"""

    @method_decorator(require_auth)
    def get(self, request):
        """
        获取向量数据库状态

        查询参数：
        - file_id: 可选，只查特定文件状态
        """
        try:
            user = request.user
            file_id_str = request.query_params.get("file_id")

            if file_id_str:
                # 查询单个文件状态
                file_id = int(file_id_str)
                
                # 从 IndexerManager 获取索引状态（进度）
                index_status = IndexerManager.get_status(file_id)
                
                # 从 VectorStore 获取索引结果信息
                file_info = VectorStore.get_file_info(file_id)
                
                return Response({
                    "status": "success",
                    "file_id": file_id,
                    "indexed": file_info["indexed"],
                    "chunk_count": file_info["chunk_count"],
                    "index_status": index_status  # 包含进度、状态等
                })
            else:
                # 查询全局状态
                total_docs = VectorStore.count()
                all_index_status = IndexerManager.get_all_status()
                
                return Response({
                    "status": "success",
                    "total_documents": total_docs,
                    "all_index_status": all_index_status  # 所有文件的索引状态
                })

        except ValueError as e:
            return Response({
                "status": "failed",
                "detail": "file_id 必须是整数"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"❌ 状态接口错误: {e}")
            return Response({
                "status": "failed",
                "detail": f"服务器错误: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------- 测试接口（可选） -------------------
@method_decorator(csrf_exempt, name='dispatch')
class TestRetrieveView(APIView):
    """测试检索功能"""

    @method_decorator(require_auth)
    def post(self, request):
        """
        测试检索

        请求参数：
        {
            "file_id": 3,
            "query": "这次会议的主要决定是什么？"
        }
        """
        try:
            user = request.user
            data = request.data
            file_id = data.get("file_id")
            query = data.get("query", "")

            results = Retriever.search(query, file_id=file_id)

            return Response({
                "status": "success",
                "results": results
            })

        except Exception as e:
            logger.error(f"❌ 检索测试错误: {e}")
            return Response({
                "status": "failed",
                "detail": f"服务器错误: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
