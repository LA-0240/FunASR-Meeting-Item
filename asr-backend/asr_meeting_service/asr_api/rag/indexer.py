# ==========================================
# 索引器 - 构建向量数据库
# ==========================================
"""
会议数据索引器
==============

本模块负责将会议相关数据（逐字稿、会议纪要、摘要、分段等）索引到向量数据库中，
为后续的RAG检索提供数据基础。

主要功能：
    - 文件索引: 索引单个会议文件的所有相关数据
    - 批量索引: 索引指定用户的所有文件
    - 语义分块: 按句子边界智能切分文本
    - 状态查询: 获取索引状态信息

索引数据类型：
    - 逐字稿 (transcript): 会议的完整文本记录
    - 会议纪要 (summary): 会议的总结内容
    - 会议摘要 (abstract): 会议的简短摘要
    - 分段内容 (segment): 会议的时间分段内容
    - 分段摘要 (segment_summary): 会议分段的摘要

核心类：
    Indexer: 会议数据索引器类

使用方式：
    from asr_api.rag import Indexer
    # 索引单个文件
    Indexer.index_file(file_id=1, rebuild=True)
    # 索引用户所有文件
    Indexer.index_all_user_files(user_id=1)

注意事项：
    - 索引过程会自动进行文本向量化
    - 支持重建索引（先删除后添加）
    - 逐字稿会进行语义分块处理
"""
from typing import List, Dict, Any, Optional
from .config import RAGConfig
from .vector_store import VectorStore
from asr_api.models import (
    UploadedFile,
    Transcription,
    MeetingSummary,
    MeetingSegment
)


class Indexer:
    """
    会议数据索引器类
    
    负责从数据库中读取会议相关数据（逐字稿、会议纪要、分段等），
    进行适当的文本分块处理，然后索引到向量数据库中。
    
    索引流程：
        1. 读取数据库中的会议数据
        2. 对长文本进行语义分块
        3. 调用VectorStore进行向量化和存储
    """

    @classmethod
    def index_file(cls, file_id: int, rebuild: bool = False) -> int:
        """
        索引单个会议文件
        
        将指定文件的所有相关数据（逐字稿、纪要、分段等）索引到向量数据库。
        
        Args:
            file_id: 文件ID
            rebuild: 是否先删除旧索引再重建

        Returns:
            int: 索引成功的文档块数量，失败返回0
            
        Examples:
            >>> count = Indexer.index_file(file_id=1, rebuild=True)
            >>> print(f"索引了 {count} 个文档块")
        """
        print(f"📚 开始索引文件ID: {file_id}")

        try:
            # 获取文件
            file_obj = UploadedFile.objects.get(id=file_id)
            user_id = file_obj.user.id

            # 如果需要重建，先删除旧索引
            if rebuild:
                VectorStore.delete_by_file_id(file_id)

            # 准备文档列表
            documents = []
            metadatas = []

            # ========== 1. 索引逐字稿 ==========
            try:
                transcription = Transcription.objects.get(file=file_obj)
                if transcription.transcription_text:
                    chunks = cls._chunk_text(transcription.transcription_text)
                    for i, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({
                            "file_id": file_id,
                            "user_id": user_id,
                            "file_name": file_obj.original_name,
                            "data_type": "transcript",
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "meeting_type": file_obj.meeting_type or "",
                            "upload_time": file_obj.upload_time.isoformat() if file_obj.upload_time else ""
                        })
                    print(f"   ✅ 逐字稿: {len(chunks)} 块（语义分段）")
            except Transcription.DoesNotExist:
                print("   ⚠️  未找到逐字稿")

            # ========== 2. 索引会议纪要 ==========
            try:
                summary = MeetingSummary.objects.get(file=file_obj)
                if summary.summary_text:
                    documents.append(summary.summary_text)
                    metadatas.append({
                        "file_id": file_id,
                        "user_id": user_id,
                        "file_name": file_obj.original_name,
                        "data_type": "summary",
                        "chunk_index": 0,
                        "total_chunks": 1,
                        "meeting_type": file_obj.meeting_type or "",
                        "upload_time": file_obj.upload_time.isoformat() if file_obj.upload_time else ""
                    })
                    print("   ✅ 会议纪要: 1 块")

                if summary.abstract_text:
                    documents.append(summary.abstract_text)
                    metadatas.append({
                        "file_id": file_id,
                        "user_id": user_id,
                        "file_name": file_obj.original_name,
                        "data_type": "abstract",
                        "chunk_index": 0,
                        "total_chunks": 1,
                        "meeting_type": file_obj.meeting_type or "",
                        "upload_time": file_obj.upload_time.isoformat() if file_obj.upload_time else ""
                    })
                    print("   ✅ 会议摘要: 1 块")
            except MeetingSummary.DoesNotExist:
                print("   ⚠️  未找到会议纪要")

            # ========== 3. 索引会议分段 ==========
            segments = MeetingSegment.objects.filter(file=file_obj).order_by("segment_index")
            for seg in segments:
                # 索引分段内容
                if seg.content:
                    documents.append(seg.content)
                    metadatas.append({
                        "file_id": file_id,
                        "user_id": user_id,
                        "file_name": file_obj.original_name,
                        "data_type": "segment",
                        "segment_index": seg.segment_index,
                        "title": seg.title or "",
                        "start_time": seg.start_time or 0,
                        "end_time": seg.end_time or 0,
                        "meeting_type": file_obj.meeting_type or "",
                        "upload_time": file_obj.upload_time.isoformat() if file_obj.upload_time else ""
                    })

                # 索引分段总结
                if seg.summary:
                    documents.append(f"【{seg.title}】{seg.summary}")
                    metadatas.append({
                        "file_id": file_id,
                        "user_id": user_id,
                        "file_name": file_obj.original_name,
                        "data_type": "segment_summary",
                        "segment_index": seg.segment_index,
                        "title": seg.title or "",
                        "start_time": seg.start_time or 0,
                        "end_time": seg.end_time or 0,
                        "meeting_type": file_obj.meeting_type or "",
                        "upload_time": file_obj.upload_time.isoformat() if file_obj.upload_time else ""
                    })

            print(f"   ✅ 会议分段: {len(segments)} 段")

            # ========== 4. 添加到向量数据库 ==========
            if documents:
                VectorStore.add_documents(documents, metadatas)
                print(f"🎉 文件ID={file_id} 索引完成! 总计: {len(documents)} 块")
                return len(documents)
            else:
                print("⚠️  没有可索引的内容")
                return 0

        except UploadedFile.DoesNotExist:
            print(f"❌ 文件ID={file_id} 不存在")
            return 0
        except Exception as e:
            print(f"❌ 索引失败: {e}")
            import traceback
            traceback.print_exc()
            return 0

    @classmethod
    def index_all_user_files(cls, user_id: int, rebuild: bool = False) -> int:
        """
        索引指定用户的所有文件
        
        批量索引用户的所有会议文件，适合初始化或重建索引。
        
        Args:
            user_id: 用户ID
            rebuild: 是否对每个文件都重建索引

        Returns:
            int: 索引的总文档块数
            
        Examples:
            >>> total = Indexer.index_all_user_files(user_id=1, rebuild=False)
            >>> print(f"共索引 {total} 个文档块")
        """
        print(f"📚 开始索引用户ID={user_id} 的所有文件")
        total_chunks = 0

        files = UploadedFile.objects.filter(user_id=user_id)
        for file_obj in files:
            total_chunks += cls.index_file(file_obj.id, rebuild)

        print(f"🎉 用户ID={user_id} 索引完成! 总计: {total_chunks} 块")
        return total_chunks

    @classmethod
    def _chunk_text(cls, text: str) -> List[str]:
        """
        按句子语义分块（中文优化）
        
        将长文本按句子边界切分，然后组合成不超过指定大小的块，
        保持句子的完整性，避免语义被切断。
        
        中文句子结束标点：。！？；\n
        
        Args:
            text: 待分块的长文本

        Returns:
            List[str]: 文本块列表
            
        Examples:
            >>> chunks = Indexer._chunk_text("长文本内容...")
            >>> for chunk in chunks:
            ...     print(len(chunk))
        """
        if not text:
            return []

        chunk_size = RAGConfig.CHUNK_SIZE

        # 1. 先把文本按句子切分
        # 中文句子结束标点：。！？；\n
        sentences = []
        current = ""
        for char in text:
            current += char
            if char in ["。", "！", "？", "；", "\n"]:
                if current.strip():
                    sentences.append(current.strip())
                current = ""
        # 添加最后一句
        if current.strip():
            sentences.append(current.strip())

        if not sentences:
            return [text[:chunk_size]]

        # 2. 把句子组合成块（保持句子完整性）
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            # 如果当前块加上这个句子超过size，就先保存当前块
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            # 添加句子
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @classmethod
    def get_index_status(cls, file_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取索引状态信息
        
        Args:
            file_id: 按文件过滤（可选，暂未实现）
            user_id: 按用户过滤（可选，暂未实现）

        Returns:
            Dict[str, Any]: 索引状态信息，包含：
                - total_documents: 总文档数
                - chroma_dir: ChromaDB存储目录
        """
        total_count = VectorStore.count()
        return {
            "total_documents": total_count,
            "chroma_dir": RAGConfig.CHROMA_PERSIST_DIR
        }
