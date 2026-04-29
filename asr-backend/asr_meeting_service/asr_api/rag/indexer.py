# ==========================================
# 索引器 - 构建向量数据库

# ==========================================
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
    """会议数据索引器"""

    @classmethod
    def index_file(cls, file_id: int, rebuild: bool = False) -> int:
        """
        索引单个会议文件

        Args:
            file_id: 文件ID
            rebuild: 是否先删除旧索引

        Returns:
            索引的文档块数量
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

        Args:
            user_id: 用户ID
            rebuild: 是否重建

        Returns:
            索引的总块数
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

        Args:
            text: 长文本

        Returns:
            分块列表
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
        获取索引状态

        Args:
            file_id: 按文件过滤（可选）
            user_id: 按用户过滤（可选）

        Returns:
            状态信息
        """
        total_count = VectorStore.count()
        return {
            "total_documents": total_count,
            "chroma_dir": RAGConfig.CHROMA_PERSIST_DIR
        }
