"""
索引任务状态管理器模块
管理异步索引任务的状态和进度跟踪
"""
# ==========================================
# 索引状态管理器
# ==========================================
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IndexerManager:
    """索引任务管理器，管理异步索引任务和状态"""
    
    # 全局索引状态字典 {file_id: {"status": "idle|indexing|done|error", "progress": 0-100, "error": "...", "start_time": datetime, "end_time": datetime}}
    _index_status = {}
    # 线程锁，保证状态更新的线程安全
    _lock = threading.Lock()
    # 活跃的索引线程
    _active_threads = {}
    
    @classmethod
    def get_status(cls, file_id):
        """获取文件的索引状态
        Args:
            file_id: 文件ID
        Returns:
            dict: 索引状态字典
        """
        with cls._lock:
            return cls._index_status.get(file_id, {
                "status": "idle",
                "progress": 0,
                "error": None,
                "start_time": None,
                "end_time": None
            })
    
    @classmethod
    def is_indexing(cls, file_id):
        """检查文件是否正在索引中
        Args:
            file_id: 文件ID
        Returns:
            bool: 是否正在索引
        """
        with cls._lock:
            status = cls._index_status.get(file_id, {}).get("status")
            return status == "indexing"
    
    @classmethod
    def start_indexing(cls, file_id):
        """开始索引，返回是否可以开始（如果正在索引则返回False）
        Args:
            file_id: 文件ID
        Returns:
            bool: 是否成功启动索引
        """
        with cls._lock:
            current_status = cls._index_status.get(file_id, {}).get("status")
            if current_status == "indexing":
                logger.warning(f"文件{file_id}正在索引中，跳过重复索引请求")
                return False
            
            # 设置新状态
            cls._index_status[file_id] = {
                "status": "indexing",
                "progress": 0,
                "error": None,
                "start_time": datetime.now(),
                "end_time": None
            }
            return True
    
    @classmethod
    def update_progress(cls, file_id, progress):
        """更新索引进度
        Args:
            file_id: 文件ID
            progress: 进度值 (0-100)
        """
        with cls._lock:
            if file_id in cls._index_status:
                cls._index_status[file_id]["progress"] = progress
    
    @classmethod
    def finish_indexing(cls, file_id, success=True, error_msg=None):
        """完成索引
        Args:
            file_id: 文件ID
            success: 是否成功
            error_msg: 错误信息（如果失败）
        """
        with cls._lock:
            if file_id in cls._index_status:
                if success:
                    cls._index_status[file_id]["status"] = "done"
                    cls._index_status[file_id]["progress"] = 100
                else:
                    cls._index_status[file_id]["status"] = "error"
                    cls._index_status[file_id]["error"] = error_msg
                cls._index_status[file_id]["end_time"] = datetime.now()
    
    @classmethod
    def reset_status(cls, file_id):
        """重置文件索引状态
        Args:
            file_id: 文件ID
        """
        with cls._lock:
            if file_id in cls._index_status:
                cls._index_status[file_id] = {
                    "status": "idle",
                    "progress": 0,
                    "error": None,
                    "start_time": None,
                    "end_time": None
                }
    
    @classmethod
    def get_all_status(cls):
        """获取所有文件的索引状态
        Returns:
            dict: 所有文件的索引状态字典副本
        """
        with cls._lock:
            return cls._index_status.copy()
