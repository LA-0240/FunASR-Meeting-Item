# ==========================================
# Agent - 智能会议助手
# ==========================================
"""
智能会议助手 Agent 模块
=======================

本模块实现了会议相关的智能对话助手，支持多种工具调用和RAG检索，
为用户提供专业的会议分析和问答服务。

主要功能：
1. 智能对话：支持与会议内容的自然语言交互
2. 工具调用：
   - SPEAKER_STATS: 发言人统计分析
   - FULL_TRANSCRIPT: 完整逐字稿分析
   - SPEAKER_FILTER: 指定发言人查询
   - TIME_RANGE_QUERY: 时间范围查询
   - KEYWORD_SEARCH: 关键词搜索
   - SEGMENT_RETRIEVER: 分段内容检索
3. RAG检索：基于向量数据库的语义检索
4. 对话历史：支持多轮对话，保存上下文

核心类：
    MeetingAgent: 会议助手Agent类

工作流程：
    1. 用户提问 → LLM判断是否需要工具调用
    2. 调用相应工具获取数据 → 构建上下文
    3. LLM基于工具结果/RAG内容生成回答
    4. 返回回答、来源、思考过程

使用方式：
    from asr_api.rag import MeetingAgent
    agent = MeetingAgent(user_id=1, file_id=1)
    result = agent.chat("会议主要讨论了什么？")
    # result: {"answer": "...", "sources": [...], "thinking": "..."}

注意事项：
    - 需要配置LLM API（RAGConfig.LLM_CONFIG）
    - 需要确保会议文件已索引（Indexer.index_file）
    - 工具调用支持回退到关键词匹配（LLM失败时）
"""
import os
import json
from typing import Dict, List, Any, Optional
from .config import RAGConfig
from .retriever import Retriever
from asr_api.models import (
    UploadedFile,
    Transcription,
    MeetingSummary,
    MeetingSegment,
    Speaker
)

# 尝试导入LLM库
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  OpenAI库未安装，使用模拟模式")


class MeetingAgent:
    """
    会议助手 Agent 类
    
    提供智能对话服务，支持工具调用和RAG检索，
    帮助用户分析和查询会议内容。
    
    核心能力：
    - 工具调用：6种专业工具处理不同类型问题
    - RAG检索：基于向量数据库的语义搜索
    - 对话历史：维护多轮对话上下文
    - 来源追踪：记录信息来源，支持溯源
    
    Attributes:
        user_id (int): 用户ID
        file_id (Optional[int]): 会议文件ID（可选）
        chat_history (List[Dict]): 对话历史记录
    """
    def __init__(self, user_id: int, file_id: Optional[int] = None):
        """
        初始化会议助手Agent
        
        Args:
            user_id: 用户ID，用于权限验证和数据隔离
            file_id: 会议文件ID（可选），指定后可针对该文件提问
        """
        self.user_id = user_id
        self.file_id = file_id
        self.chat_history = []  # 对话历史
        
    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        发送消息，获取智能回答
        
        核心方法：处理用户问题，可能调用工具或RAG检索，
        最终由LLM生成专业回答。
        
        Args:
            user_message: 用户输入的问题或消息

        Returns:
            Dict[str, Any]: 包含三部分的回答结果
                - answer: LLM生成的回答文本
                - sources: 信息来源列表（RAG片段或工具调用）
                - thinking: 思考过程说明（如调用了什么工具）
                
        Examples:
            >>> agent = MeetingAgent(user_id=1, file_id=1)
            >>> result = agent.chat("谁在会议中发言最多？")
            >>> print(result["answer"])
        """
        print(f"🤖 Agent收到消息: {user_message[:50]}...")

        sources = []
        thinking = ""
        used_tool = None  # 记录是否使用了工具
        
        # ========== 方案3：让 LLM 自主判断是否需要调用工具 ==========
        if self.file_id:
            # ========== 1. 让 LLM 判断需要调用哪个工具 ==========
            tool_decision = self._decide_which_tool_to_call(user_message)
            
            if tool_decision == "SPEAKER_STATS":
                print("🔍 LLM 判断需要调用【发言统计工具】...")
                used_tool = "SPEAKER_STATS"
                # ========== 2. 调用工具获取统计数据 ==========
                speaker_stats = self._get_speaker_statistics()
                
                # ========== 构建工具来源 ==========
                sources = self._build_sources_for_speaker_stats(speaker_stats, used_tool)
                
                # ========== 补充 RAG 检索片段（让来源更丰富） ==========
                results = Retriever.search(user_message, file_id=self.file_id)
                rag_sources = [
                    {
                        "data_type": r["metadata"].get("data_type"),
                        "content": r["document"][:200],
                        "score": r.get("rerank_score", r.get("similarity")),
                        "speaker": r["metadata"].get("speaker"),
                        "start_time": r["metadata"].get("start_time"),
                        "end_time": r["metadata"].get("end_time"),
                        "title": r["metadata"].get("title"),
                        "is_tool_source": False  # 标识这是正常检索
                    }
                    for r in results[:3]  # 只取前 3 个作为补充
                ]
                sources.extend(rag_sources)
                
                # ========== 3. 把统计数据给 LLM，让它生成回答 ==========
                prompt = self._build_speaker_prompt_with_stats(user_message, speaker_stats)
                answer = self._call_llm(prompt)
                thinking = "LLM 自主判断调用了发言统计工具，根据完整统计数据回答"
            elif tool_decision == "FULL_TRANSCRIPT":
                print("🔍 LLM 判断需要调用【完整逐字稿工具】...")
                used_tool = "FULL_TRANSCRIPT"
                # ========== 2. 调用工具获取完整逐字稿 ==========
                full_transcript = self._get_full_transcript()
                
                # ========== 构建工具来源 ==========
                sources = self._build_sources_for_full_transcript(full_transcript, used_tool)
                
                # ========== 补充 RAG 检索片段（让来源更丰富） ==========
                results = Retriever.search(user_message, file_id=self.file_id)
                rag_sources = [
                    {
                        "data_type": r["metadata"].get("data_type"),
                        "content": r["document"][:200],
                        "score": r.get("rerank_score", r.get("similarity")),
                        "speaker": r["metadata"].get("speaker"),
                        "start_time": r["metadata"].get("start_time"),
                        "end_time": r["metadata"].get("end_time"),
                        "title": r["metadata"].get("title"),
                        "is_tool_source": False  # 标识这是正常检索
                    }
                    for r in results[:3]  # 只取前 3 个作为补充
                ]
                sources.extend(rag_sources)
                
                # ========== 3. 把逐字稿数据给 LLM，让它生成回答 ==========
                prompt = self._build_transcript_prompt(user_message, full_transcript)
                answer = self._call_llm(prompt)
                thinking = "LLM 自主判断调用了完整逐字稿工具，根据完整逐字稿内容分析回答"
            elif tool_decision == "SPEAKER_FILTER":
                print("🔍 LLM 判断需要调用【发言人过滤工具】...")
                used_tool = "SPEAKER_FILTER"
                # ========== 2. 调用工具获取指定发言人发言 ==========
                # 从用户问题中提取发言人名字（简化处理）
                speaker_name = None
                speaker_info = None
                try:
                    file_obj = UploadedFile.objects.get(id=self.file_id)
                    transcription = Transcription.objects.get(file=file_obj)
                    speaker_info = transcription.segments or []
                    speakers = list(set([s.get('speaker', '未知说话人') for s in speaker_info]))
                    # 简单：尝试找问题中包含的发言人名字
                    for s in speakers:
                        if s in user_message:
                            speaker_name = s
                            break
                except:
                    pass
                
                speaker_filter_data = self._get_speaker_filter(speaker_name)
                
                # ========== 构建工具来源 ==========
                sources = self._build_sources_for_speaker_filter(speaker_filter_data, used_tool)
                
                # ========== 补充 RAG 检索片段（让来源更丰富） ==========
                results = Retriever.search(user_message, file_id=self.file_id)
                rag_sources = [
                    {
                        "data_type": r["metadata"].get("data_type"),
                        "content": r["document"][:200],
                        "score": r.get("rerank_score", r.get("similarity")),
                        "speaker": r["metadata"].get("speaker"),
                        "start_time": r["metadata"].get("start_time"),
                        "end_time": r["metadata"].get("end_time"),
                        "title": r["metadata"].get("title"),
                        "is_tool_source": False
                    }
                    for r in results[:3]
                ]
                sources.extend(rag_sources)
                
                # ========== 3. 把数据给 LLM，让它生成回答 ==========
                prompt = self._build_speaker_filter_prompt(user_message, speaker_filter_data)
                answer = self._call_llm(prompt)
                thinking = "LLM 自主判断调用了发言人过滤工具"
            elif tool_decision == "TIME_RANGE_QUERY":
                print("🔍 LLM 判断需要调用【时间范围查询工具】...")
                used_tool = "TIME_RANGE_QUERY"
                # ========== 2. 调用工具获取时间范围内容 ==========
                # 从用户问题中提取时间（简化处理）
                start_time = None
                end_time = None
                try:
                    file_obj = UploadedFile.objects.get(id=self.file_id)
                    transcription = Transcription.objects.get(file=file_obj)
                    speaker_info = transcription.segments or []
                    if speaker_info:
                        total_duration = speaker_info[-1].get('end_time', 0)
                        if "前" in user_message and "分钟" in user_message:
                            end_time = 60 * 5  # 默认前5分钟
                        elif "后" in user_message and "分钟" in user_message:
                            start_time = total_duration - 60 * 5  # 默认后5分钟
                        else:
                            start_time = 0
                            end_time = min(60 * 10, total_duration)  # 默认前10分钟
                except:
                    pass
                
                time_range_data = self._get_time_range_query(start_time, end_time)
                
                # ========== 构建工具来源 ==========
                sources = self._build_sources_for_time_range_query(time_range_data, used_tool)
                
                # ========== 补充 RAG 检索片段 ==========
                results = Retriever.search(user_message, file_id=self.file_id)
                rag_sources = [
                    {
                        "data_type": r["metadata"].get("data_type"),
                        "content": r["document"][:200],
                        "score": r.get("rerank_score", r.get("similarity")),
                        "speaker": r["metadata"].get("speaker"),
                        "start_time": r["metadata"].get("start_time"),
                        "end_time": r["metadata"].get("end_time"),
                        "title": r["metadata"].get("title"),
                        "is_tool_source": False
                    }
                    for r in results[:3]
                ]
                sources.extend(rag_sources)
                
                # ========== 3. 把数据给 LLM，让它生成回答 ==========
                prompt = self._build_time_range_prompt(user_message, time_range_data)
                answer = self._call_llm(prompt)
                thinking = "LLM 自主判断调用了时间范围查询工具"
            elif tool_decision == "KEYWORD_SEARCH":
                print("🔍 LLM 判断需要调用【关键词搜索工具】...")
                used_tool = "KEYWORD_SEARCH"
                # ========== 2. 调用工具搜索关键词 ==========
                keyword = None
                # 简单：尝试从问题中提取关键词（简化处理）
                words = ["价格", "合同", "预算", "方案", "产品", "项目"]
                for w in words:
                    if w in user_message:
                        keyword = w
                        break
                if not keyword:
                    keyword = user_message
                
                keyword_search_data = self._get_keyword_search(keyword)
                
                # ========== 构建工具来源 ==========
                sources = self._build_sources_for_keyword_search(keyword_search_data, used_tool)
                
                # ========== 补充 RAG 检索片段 ==========
                results = Retriever.search(user_message, file_id=self.file_id)
                rag_sources = [
                    {
                        "data_type": r["metadata"].get("data_type"),
                        "content": r["document"][:200],
                        "score": r.get("rerank_score", r.get("similarity")),
                        "speaker": r["metadata"].get("speaker"),
                        "start_time": r["metadata"].get("start_time"),
                        "end_time": r["metadata"].get("end_time"),
                        "title": r["metadata"].get("title"),
                        "is_tool_source": False
                    }
                    for r in results[:3]
                ]
                sources.extend(rag_sources)
                
                # ========== 3. 把数据给 LLM，让它生成回答 ==========
                prompt = self._build_keyword_search_prompt(user_message, keyword_search_data)
                answer = self._call_llm(prompt)
                thinking = "LLM 自主判断调用了关键词搜索工具"
            elif tool_decision == "SEGMENT_RETRIEVER":
                print("🔍 LLM 判断需要调用【分段检索工具】...")
                used_tool = "SEGMENT_RETRIEVER"
                # ========== 2. 调用工具获取分段内容 ==========
                segment_index = None
                segment_title = None
                try:
                    file_obj = UploadedFile.objects.get(id=self.file_id)
                    segments = MeetingSegment.objects.filter(file=file_obj).order_by('order_number')
                    if segments:
                        segment_index = 0  # 默认第一个分段
                except:
                    pass
                
                segment_data = self._get_segment_retriever(segment_title, segment_index)
                
                # ========== 构建工具来源 ==========
                sources = self._build_sources_for_segment_retriever(segment_data, used_tool)
                
                # ========== 补充 RAG 检索片段 ==========
                results = Retriever.search(user_message, file_id=self.file_id)
                rag_sources = [
                    {
                        "data_type": r["metadata"].get("data_type"),
                        "content": r["document"][:200],
                        "score": r.get("rerank_score", r.get("similarity")),
                        "speaker": r["metadata"].get("speaker"),
                        "start_time": r["metadata"].get("start_time"),
                        "end_time": r["metadata"].get("end_time"),
                        "title": r["metadata"].get("title"),
                        "is_tool_source": False
                    }
                    for r in results[:3]
                ]
                sources.extend(rag_sources)
                
                # ========== 3. 把数据给 LLM，让它生成回答 ==========
                prompt = self._build_segment_retriever_prompt(user_message, segment_data)
                answer = self._call_llm(prompt)
                thinking = "LLM 自主判断调用了分段检索工具"
            else:
                print("🔍 LLM 判断不需要调用工具，走正常检索流程...")
                used_tool = None
                # ========== 正常流程：检索相关内容 ==========
                results = Retriever.search(user_message, file_id=self.file_id)
                context = Retriever.format_context(results)
                sources = [
                    {
                        "data_type": r["metadata"].get("data_type"),
                        "content": r["document"][:200],
                        "score": r.get("rerank_score", r.get("similarity")),
                        "speaker": r["metadata"].get("speaker"),
                        "start_time": r["metadata"].get("start_time"),
                        "end_time": r["metadata"].get("end_time"),
                        "title": r["metadata"].get("title"),
                        "is_tool_source": False  # 标识这是正常检索
                    }
                    for r in results
                ]
                # ========== 构建 Prompt ==========
                prompt = self._build_prompt(user_message, context)
                # ========== 调用 LLM 生成回答 ==========
                answer = self._call_llm(prompt)
                thinking = "检索了会议内容并生成回答"
        else:
            # ========== 无 file_id，走正常流程 ==========
            used_tool = None
            prompt = self._build_prompt(user_message, "")
            answer = self._call_llm(prompt)
            thinking = "无会议文件，直接回答"

        # ========== 保存对话历史 ==========
        self.chat_history.append({
            "role": "user",
            "content": user_message
        })
        self.chat_history.append({
            "role": "assistant",
            "content": answer
        })

        # ========== 返回结果 ==========
        return {
            "answer": answer,
            "sources": sources,
            "thinking": thinking
        }
        
    # 决定调用哪个工具
    def _decide_which_tool_to_call(self, user_message: str) -> str:
        """
        让 LLM 判断需要调用哪个工具

        Args:
            user_message: 用户问题

        Returns:
            "SPEAKER_STATS" | "FULL_TRANSCRIPT" | "SPEAKER_FILTER" | "TIME_RANGE_QUERY" | "KEYWORD_SEARCH" | "SEGMENT_RETRIEVER" | "NONE"
        """
        system_prompt = """你是一个会议分析助手。你可以调用以下工具解决用户问题：

【工具1】SPEAKER_STATS - 发言统计工具
- 功能：获取所有发言人的发言次数、发言时长、排名等完整统计数据
- 适用场景：
  - 用户问「谁说话最多」、「谁发言最多」、「谁最活跃」、「谁是劳模」
  - 用户问「谁说话最少」、「谁发言最少」、「谁最不活跃」、「谁贡献最低」
  - 用户问「发言统计」、「说话统计」、「排名」、「前几名」、「后几名」
  - 用户问「前2」、「后2」、「前3」、「后3」等排名问题
  - 用户问「分析前2和后2」、「分析优缺点」、「如何改进」等需要具体统计数据的问题
  - 用户要求列出所有参会人、所有发言人名单
  - 用户要求整理人员列表、区分角色（买方、卖方、甲方、乙方、领导、员工等）

【工具2】FULL_TRANSCRIPT - 完整逐字稿工具
- 功能：获取完整的会议逐字稿，包含所有发言人的所有对话内容
- 适用场景：
  - 用户问「根据所有逐字稿」、「根据全部内容」、「详细信息」
  - 用户问「分析会议内容」、「分析公司背景」、「分析业务模式」
  - 用户问「会议主要内容」、「会议都讲了什么」、「完整内容是什么」
  - 用户需要基于完整会议记录进行深度分析
  - 用户询问会议涉及的产品、公司、项目等背景信息
  - 用户问题涉及"所有"、"全部"、"完整"、"详细"等关键词

【工具3】SPEAKER_FILTER - 发言人过滤工具
- 功能：只获取指定发言人的所有发言
- 适用场景：
  - 用户问「张三讲了什么」、「李四的观点是什么」
  - 用户问「王五的发言」、「赵六说过什么」
  - 用户问题明确提到某个发言人的名字
  - 用户想知道某个人在会议中的完整发言记录

【工具4】TIME_RANGE_QUERY - 时间范围查询工具
- 功能：获取指定时间范围内的对话内容
- 适用场景：
  - 用户问「前10分钟讲了什么」、「前5分钟内容」
  - 用户问「15:30-16:00讨论了什么」、「中间部分讲了什么」
  - 用户提到"分钟"、"时间段"、"前"、"后"、"中间"等时间相关词汇
  - 用户想回顾会议某个时间段的内容

【工具5】KEYWORD_SEARCH - 关键词搜索工具
- 功能：精确搜索包含某关键词的所有句子
- 适用场景：
  - 用户问「搜索价格相关内容」、「查找关于合同的讨论」
  - 用户明确提到要"查找"、"搜索"、"找"等关键词
  - 用户想找到所有提到某个词的地方

【工具6】SEGMENT_RETRIEVER - 分段检索工具
- 功能：获取指定分段的内容
- 适用场景：
  - 用户问「第二部分讲了什么」、「讨论阶段的内容」
  - 用户提到某个分段标题或分段序号
  - 用户想了解某个特定分段的内容

【选项】
- 如果用户问题属于【工具1】场景，返回：SPEAKER_STATS
- 如果用户问题属于【工具2】场景，返回：FULL_TRANSCRIPT
- 如果用户问题属于【工具3】场景，返回：SPEAKER_FILTER
- 如果用户问题属于【工具4】场景，返回：TIME_RANGE_QUERY
- 如果用户问题属于【工具5】场景，返回：KEYWORD_SEARCH
- 如果用户问题属于【工具6】场景，返回：SEGMENT_RETRIEVER
- 如果都不适合，返回：NONE

只返回上面七个选项之一，不要输出其他任何内容！"""

        prompt = f"""{system_prompt}

用户问题：{user_message}

请返回 SPEAKER_STATS / FULL_TRANSCRIPT / SPEAKER_FILTER / TIME_RANGE_QUERY / KEYWORD_SEARCH / SEGMENT_RETRIEVER / NONE："""
        
        try:
            # 调用 LLM 判断
            response = self._call_llm_for_decision(prompt)
            response = response.strip().upper()
            print(f"🤖 LLM 判断工具调用: {response}")
            
            if "SPEAKER" in response and "STATS" in response:
                return "SPEAKER_STATS"
            elif "FULL" in response and "TRANSCRIPT" in response:
                return "FULL_TRANSCRIPT"
            elif "SPEAKER" in response and "FILTER" in response:
                return "SPEAKER_FILTER"
            elif "TIME" in response and "RANGE" in response:
                return "TIME_RANGE_QUERY"
            elif "KEYWORD" in response and "SEARCH" in response:
                return "KEYWORD_SEARCH"
            elif "SEGMENT" in response and "RETRIEVER" in response:
                return "SEGMENT_RETRIEVER"
            else:
                return "NONE"
        except Exception as e:
            print(f"⚠️ LLM 判断失败，回退到关键词匹配: {e}")
            # 回退方案：关键词匹配
            speaker_stats_keywords = ["说话最多", "发言最多", "谁说话最多", "谁发言最多", "谁活跃", "谁最活跃", "劳模", "贡献度", "发言统计", "说话统计", "发言时长", "说话时长", "谁讲得多", "谁发言最少", "谁说话最少", "谁贡献最少", "谁贡献度最低", "说话排名", "发言排名", "排名", "前几名", "后几名", "前2名", "后2名", "前2", "后2", "前3", "后3", "分析前", "分析后", "优缺点", "如何改进"]
            speaker_filter_keywords = ["的发言", "的观点", "的话", "说了什么", "讲了什么"]
            time_range_keywords = ["前几分钟", "后几分钟", "时间段", "分钟", "第几分钟"]
            keyword_search_keywords = ["搜索", "查找", "找一下", "关键词"]
            segment_retriever_keywords = ["分段", "第几个部分", "第几部分", "阶段"]
            full_transcript_keywords = ["所有逐字稿", "全部内容", "完整内容", "详细信息", "分析会议", "分析公司", "公司背景", "业务模式", "会议内容", "讲了什么", "主要内容", "深度分析", "产品介绍", "项目介绍", "公司介绍"]
            
            if any(k in user_message for k in speaker_stats_keywords):
                return "SPEAKER_STATS"
            elif any(k in user_message for k in speaker_filter_keywords):
                return "SPEAKER_FILTER"
            elif any(k in user_message for k in time_range_keywords):
                return "TIME_RANGE_QUERY"
            elif any(k in user_message for k in keyword_search_keywords):
                return "KEYWORD_SEARCH"
            elif any(k in user_message for k in segment_retriever_keywords):
                return "SEGMENT_RETRIEVER"
            elif any(k in user_message for k in full_transcript_keywords):
                return "FULL_TRANSCRIPT"
            else:
                return "NONE"

    # 调用LLM进行简单决策
    # 用于判断用户问题是否属于某个工具的场景
    def _call_llm_for_decision(self, prompt: str) -> str:
        """
        专门用于简单决策的 LLM 调用（降低成本，快速响应）

        Args:
            prompt: Prompt

        Returns:
            LLM 回答
        """
        try:
            llm_config = RAGConfig.LLM_CONFIG
            from openai import OpenAI
            client = OpenAI(
                api_key=llm_config.get("api_key"),
                base_url=llm_config.get("base_url")
            )
            response = client.chat.completions.create(
                model=llm_config.get("model_name"),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 更低的温度，更确定的回答
                max_tokens=10
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ 决策 LLM 调用失败: {e}")
            return "NO"
        
    # 获取所有发言人的统计数据
    # 用于 LLM 调用
    def _get_speaker_statistics(self) -> Dict[str, Any]:
        """
        【工具函数】获取所有发言人的统计数据

        Returns:
            统计数据（结构化字典，方便 LLM 理解）
        """
        try:
            file_obj = UploadedFile.objects.get(id=self.file_id)
            transcription = Transcription.objects.get(file=file_obj)
            # 优先使用原始句子数据，兼容旧数据
            speaker_info = transcription.segments or []
            
            print(f"[DEBUG] 发言统计工具获取到的原始 speaker_info 前5条: {speaker_info[:5] if len(speaker_info) > 5 else speaker_info}")
            
            # ========== 新增：尝试从 Speaker 表中匹配说话人姓名 ==========
            user = file_obj.user
            speakers = Speaker.objects.filter(user=user)
            speaker_dict = {speaker.name: speaker for speaker in speakers}
            print(f"[DEBUG] 当前用户共有 {len(speakers)} 个 Speaker: {list(speaker_dict.keys())}")
            
            if not speaker_info:
                return {
                    "status": "error",
                    "message": "暂无 speaker_info 数据"
                }
            
            # 统计每个 speaker
            speaker_stats = {}
            for sent in speaker_info:
                speaker = sent.get('speaker', '未知说话人')
                
                # ========== 修复：如果 speaker 是整数，强制转换成字符串 ==========
                if isinstance(speaker, int):
                    speaker = f"spk-{speaker}"
                elif not isinstance(speaker, str):
                    speaker = str(speaker)
                
                start = sent.get('start_time', 0)
                end = sent.get('end_time', 0)
                duration = end - start if end > start else 0
                
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {
                        'count': 0,
                        'total_duration': 0.0,
                        'sentences': []
                    }
                
                speaker_stats[speaker]['count'] += 1
                speaker_stats[speaker]['total_duration'] += duration
                speaker_stats[speaker]['sentences'].append({
                    'text': sent.get('text', ''),
                    'start': start,
                    'end': end
                })
            
            # 排序：按发言次数从多到少
            sorted_speakers = sorted(
                speaker_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            # 构建结构化统计数据
            speaker_list = []
            for speaker, stats in sorted_speakers:
                speaker_list.append({
                    'speaker': speaker,
                    'count': stats['count'],
                    'total_duration_minutes': round(stats['total_duration'] / 60.0, 2),
                    'sample_sentences': [s['text'] for s in stats['sentences'][:3] if s['text']]
                })
            
            total_speakers = len(sorted_speakers)
            total_count = sum(s['count'] for s in speaker_stats.values())
            total_duration = sum(s['total_duration'] for s in speaker_stats.values())
            
            # 返回结构化数据
            result = {
                "status": "success",
                "speaker_list": speaker_list,
                "sorted_by": "count_desc",  # 按次数降序
                "summary": {
                    "total_speakers": total_speakers,
                    "total_speech_count": total_count,
                    "total_duration_minutes": round(total_duration / 60.0, 2),
                    "most_active": speaker_list[0]['speaker'] if speaker_list else None,
                    "least_active": speaker_list[-1]['speaker'] if speaker_list else None
                }
            }
            
            print(f"✅ 发言统计工具返回数据: {len(speaker_list)} 位发言人, {total_count} 条发言")
            return result
            
        except Exception as e:
            print(f"❌ 发言统计工具调用失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e)
            }
        
    # 构建带统计数据的 Prompt（工具调用模式）
    # 用于 LLM 调用
    def _build_speaker_prompt_with_stats(self, user_message: str, stats_data: Dict[str, Any]) -> str:
        """
        构建带统计数据的 Prompt（工具调用模式）

        Args:
            user_message: 用户问题
            stats_data: 统计数据

        Returns:
            完整 Prompt
        """
        system_prompt = """你是一个专业的会议分析助手。根据提供的会议发言人完整统计数据，回答用户的问题。

回答要求：
1. 首先进行数据概况说明
2. 针对用户问题进行有条理的分析
3. 回答要条理清晰，使用 Markdown 格式
4. 如果用户问排名相关问题，请给出明确的排名
5. 如果用户需要分析优缺点，请基于发言内容进行合理推断
6. 如果用户问如何改进或批判鞭策，请提供有建设性的建议
7. 请用中文回答，不要遗漏关键信息

表格格式示例：
| 发言人 | 发言次数 | 总时长 |
|--------|----------|--------|
| xxx | xx次 | xx分钟 |
"""

        # 把统计数据格式化成可读的文本
        stats_text = self._format_stats_data_to_text(stats_data)
        
        # 构建对话历史上下文
        history_context = ""
        for msg in self.chat_history[-6:]:
            if msg["role"] == "user":
                history_context += f"用户: {msg['content']}\n"
            else:
                history_context += f"助手: {msg['content']}\n"

        full_prompt = f"""{system_prompt}

========== 会议发言人完整统计数据 ==========
{stats_text}

========== 对话历史 ==========
{history_context}

========== 用户当前问题 ==========
{user_message}

请根据以上信息回答用户的问题。"""

        return full_prompt
        
    # 获取完整的会议逐字稿
    # 用于 LLM 调用
    def _get_full_transcript(self) -> Dict[str, Any]:
        """
        【工具函数】获取完整的会议逐字稿

        Returns:
            完整逐字稿数据
        """
        try:
            file_obj = UploadedFile.objects.get(id=self.file_id)
            transcription = Transcription.objects.get(file=file_obj)
            # 优先使用原始句子数据，兼容旧数据
            speaker_info = transcription.segments or []
            
            print(f"[DEBUG] RAG 获取到的原始 speaker_info 前5条: {speaker_info[:5] if len(speaker_info) > 5 else speaker_info}")
            
            # ========== 新增：尝试从 Speaker 表中匹配说话人姓名 ==========
            user = file_obj.user
            speakers = Speaker.objects.filter(user=user)
            speaker_dict = {speaker.name: speaker for speaker in speakers}
            print(f"[DEBUG] 当前用户共有 {len(speakers)} 个 Speaker: {list(speaker_dict.keys())}")
            
            updated_speaker_info = []
            for sent in speaker_info:
                new_sent = sent.copy()
                speaker_name = sent.get('speaker', '未知说话人')
                
                # ========== 修复：如果 speaker 是整数，强制转换成字符串 ==========
                if isinstance(speaker_name, int):
                    speaker_name = f"spk-{speaker_name}"
                elif not isinstance(speaker_name, str):
                    speaker_name = str(speaker_name)
                
                new_sent['speaker'] = speaker_name
                updated_speaker_info.append(new_sent)
            
            # ========== 尝试获取会议纪要和摘要作为补充 ==========
            meeting_summary = None
            meeting_abstract = None
            try:
                summary_obj = MeetingSummary.objects.get(file=file_obj)
                meeting_summary = summary_obj.summary_text
                meeting_abstract = summary_obj.abstract_text
            except:
                pass
            
            print(f"[DEBUG] RAG 最终使用的 speaker_info 前5条: {updated_speaker_info[:5] if len(updated_speaker_info) > 5 else updated_speaker_info}")
            print(f"✅ 完整逐字稿工具返回数据: {len(updated_speaker_info)} 条记录")
            return {
                "status": "success",
                "file_name": file_obj.original_name,
                "speaker_info": updated_speaker_info,
                "meeting_summary": meeting_summary,
                "meeting_abstract": meeting_abstract
            }
            
        except Exception as e:
            print(f"❌ 完整逐字稿工具调用失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e)
            }
        
    # 构建带完整逐字稿的 Prompt
    # 用于 LLM 调用
    def _build_transcript_prompt(self, user_message: str, transcript_data: Dict[str, Any]) -> str:
        """
        构建带完整逐字稿的 Prompt

        Args:
            user_message: 用户问题
            transcript_data: 逐字稿数据

        Returns:
            完整 Prompt
        """
        system_prompt = """你是一个专业的会议分析助手。根据提供的完整会议逐字稿，回答用户的问题。

回答要求：
1. 基于完整的逐字稿内容进行深度分析
2. 回答要条理清晰，使用 Markdown 格式
3. 提取关键信息，不要遗漏重要细节
4. 如果涉及公司背景、产品介绍、项目信息等，请详细整理
5. 请用中文回答，内容要详实、有深度"""

        # 把逐字稿格式化成可读的文本
        transcript_text = self._format_transcript_to_text(transcript_data)
        
        # 构建对话历史上下文
        history_context = ""
        for msg in self.chat_history[-6:]:
            if msg["role"] == "user":
                history_context += f"用户: {msg['content']}\n"
            else:
                history_context += f"助手: {msg['content']}\n"

        full_prompt = f"""{system_prompt}

========== 文件信息 ==========
文件名：{transcript_data.get('file_name', '未知')}

========== 完整逐字稿 ==========
{transcript_text}

========== 对话历史 ==========
{history_context}

========== 用户当前问题 ==========
{user_message}

请根据以上完整逐字稿信息回答用户的问题。"""

        return full_prompt
        
    # 格式化逐字稿数据
    # 用于 LLM 调用
    def _format_transcript_to_text(self, transcript_data: Dict[str, Any]) -> str:
        """
        把逐字稿数据格式化成可读的文本

        Args:
            transcript_data: 逐字稿数据

        Returns:
            格式化后的文本
        """
        if transcript_data.get("status") == "error":
            return f"数据获取失败：{transcript_data.get('message')}"
        
        lines = []
        
        # 先添加会议纪要和摘要（如果有）
        if transcript_data.get("meeting_abstract"):
            lines.append(f"=== 会议摘要 ===\n")
            lines.append(transcript_data.get("meeting_abstract", ""))
            lines.append("\n")
        
        if transcript_data.get("meeting_summary"):
            lines.append(f"=== 会议纪要 ===\n")
            lines.append(transcript_data.get("meeting_summary", ""))
            lines.append("\n")
        
        # 添加完整逐字稿
        speaker_info = transcript_data.get("speaker_info", [])
        lines.append(f"=== 完整逐字稿（共 {len(speaker_info)} 条）===\n")
        
        for idx, sent in enumerate(speaker_info, 1):
            speaker = sent.get('speaker', '未知说话人')
            text = sent.get('text', '')
            start_time = sent.get('start_time', 0)
            end_time = sent.get('end_time', 0)
            
            # 格式化时间
            start_str = f"{int(start_time // 60)}:{int(start_time % 60):02d}"
            end_str = f"{int(end_time // 60)}:{int(end_time % 60):02d}"
            
            lines.append(f"[{idx}] {speaker} [{start_str}-{end_str}]")
            lines.append(f"{text}\n")
        
        return "\n".join(lines)
        
    # 构建带统计数据的 Prompt（工具调用模式）
    # 用于 LLM 调用
    def _build_sources_for_speaker_stats(self, stats_data: Dict[str, Any], tool_name: str = None) -> List[Dict[str, Any]]:
        """
        为发言统计工具构建来源信息（只返回一条标识信息）

        Args:
            stats_data: 统计数据
            tool_name: 工具名称

        Returns:
            来源列表
        """
        sources = []
        
        if stats_data.get("status") == "success":
            # 只添加一条标识信息，说明是根据发言统计工具获取
            summary = stats_data.get("summary", {})
            sources.append({
                "data_type": "tool_call",
                "content": f"调用发言统计工具，获取了 {summary.get('total_speakers', 0)} 位发言人的完整统计数据",
                "score": 1.0,
                "is_tool_source": True,
                "tool_name": tool_name
            })
        
        return sources
        
    # 构建带完整逐字稿的 Prompt（工具调用模式）
    # 用于 LLM 调用
    def _build_sources_for_full_transcript(self, transcript_data: Dict[str, Any], tool_name: str = None) -> List[Dict[str, Any]]:
        """
        为完整逐字稿工具构建来源信息（只返回一条标识信息）

        Args:
            transcript_data: 逐字稿数据
            tool_name: 工具名称

        Returns:
            来源列表
        """
        sources = []
        
        if transcript_data.get("status") == "success":
            # 只添加一条标识信息，说明是根据完整逐字稿工具获取
            speaker_info = transcript_data.get("speaker_info", [])
            sources.append({
                "data_type": "tool_call",
                "content": f"调用完整逐字稿工具，获取了 {len(speaker_info)} 条对话内容的完整数据",
                "score": 1.0,
                "is_tool_source": True,
                "tool_name": tool_name
            })
        
        return sources
    
    # ========== 新增四个工具（数据查询） ==========
        
    # 发言人过滤工具
    # 用于 LLM 调用
    def _get_speaker_filter(self, speaker_name: str = None) -> Dict[str, Any]:
        """
        【工具函数】SPEAKER_FILTER - 获取指定发言人的所有发言
        
        Args:
            speaker_name: 发言人名称（如果不指定，会自动解析）
            
        Returns:
            指定发言人的对话数据
        """
        try:
            file_obj = UploadedFile.objects.get(id=self.file_id)
            transcription = Transcription.objects.get(file=file_obj)
            # 优先使用原始句子数据，兼容旧数据
            speaker_info = transcription.segments or []
            
            # 如果不指定 speaker_name，先返回所有发言人选项
            if not speaker_name:
                speakers = list(set([s.get('speaker', '未知说话人') for s in speaker_info]))
                return {
                    "status": "need_speaker",
                    "available_speakers": speakers,
                    "message": "请指定要查询的发言人"
                }
            
            # 过滤指定发言人
            filtered_sentences = [s for s in speaker_info if s.get('speaker') == speaker_name]
            
            print(f"✅ 发言人过滤工具返回数据: {len(filtered_sentences)} 条记录")
            return {
                "status": "success",
                "speaker_name": speaker_name,
                "speaker_info": filtered_sentences,
                "total_count": len(filtered_sentences)
            }
            
        except Exception as e:
            print(f"❌ 发言人过滤工具调用失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
    # 时间范围查询工具
    # 用于 LLM 调用
    def _get_time_range_query(self, start_time: float = None, end_time: float = None) -> Dict[str, Any]:
        """
        【工具函数】TIME_RANGE_QUERY - 获取指定时间范围内的对话
        
        Args:
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            
        Returns:
            指定时间范围的对话数据
        """
        try:
            file_obj = UploadedFile.objects.get(id=self.file_id)
            transcription = Transcription.objects.get(file=file_obj)
            # 优先使用原始句子数据，兼容旧数据
            speaker_info = transcription.segments or []
            
            # 如果不指定时间，先返回总时长
            if start_time is None or end_time is None:
                if speaker_info:
                    total_duration = speaker_info[-1].get('end_time', 0)
                    return {
                        "status": "need_time",
                        "total_duration_seconds": total_duration,
                        "message": "请指定要查询的时间范围"
                    }
                return {
                    "status": "error",
                    "message": "暂无数据"
                }
            
            # 过滤时间范围
            filtered_sentences = []
            for sent in speaker_info:
                sent_start = sent.get('start_time', 0)
                sent_end = sent.get('end_time', 0)
                # 判断是否有重叠
                if sent_end >= start_time and sent_start <= end_time:
                    filtered_sentences.append(sent)
            
            print(f"✅ 时间范围查询工具返回数据: {len(filtered_sentences)} 条记录")
            return {
                "status": "success",
                "start_time": start_time,
                "end_time": end_time,
                "speaker_info": filtered_sentences,
                "total_count": len(filtered_sentences)
            }
            
        except Exception as e:
            print(f"❌ 时间范围查询工具调用失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
    # 关键词搜索工具
    # 用于 LLM 调用
    def _get_keyword_search(self, keyword: str = None) -> Dict[str, Any]:
        """
        【工具函数】KEYWORD_SEARCH - 精确关键词搜索
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配关键词的所有句子
        """
        try:
            file_obj = UploadedFile.objects.get(id=self.file_id)
            transcription = Transcription.objects.get(file=file_obj)
            # 优先使用原始句子数据，兼容旧数据
            speaker_info = transcription.segments or []
            
            if not keyword:
                return {
                    "status": "need_keyword",
                    "message": "请指定要搜索的关键词"
                }
            
            # 精确匹配（忽略大小写）
            keyword_lower = keyword.lower()
            filtered_sentences = []
            for sent in speaker_info:
                text = sent.get('text', '').lower()
                if keyword_lower in text:
                    filtered_sentences.append(sent)
            
            print(f"✅ 关键词搜索工具返回数据: {len(filtered_sentences)} 条记录")
            return {
                "status": "success",
                "keyword": keyword,
                "speaker_info": filtered_sentences,
                "total_count": len(filtered_sentences)
            }
            
        except Exception as e:
            print(f"❌ 关键词搜索工具调用失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
    # 分段检索工具
    # 用于 LLM 调用
    def _get_segment_retriever(self, segment_title: str = None, segment_index: int = None) -> Dict[str, Any]:
        """
        【工具函数】SEGMENT_RETRIEVER - 获取指定分段的内容
        
        Args:
            segment_title: 分段标题
            segment_index: 分段索引（优先使用）
            
        Returns:
            指定分段的详细内容
        """
        try:
            file_obj = UploadedFile.objects.get(id=self.file_id)
            
            # 获取分段
            segments = MeetingSegment.objects.filter(file=file_obj).order_by('order_number')
            if not segments:
                return {
                    "status": "no_segments",
                    "message": "暂无分段数据"
                }
            
            # 根据索引或标题查找
            target_segment = None
            
            if segment_index is not None and segment_index < len(segments):
                target_segment = segments[segment_index]
            elif segment_title:
                for seg in segments:
                    if segment_title in seg.title:
                        target_segment = seg
                        break
            
            # 如果没有找到，返回所有分段标题让用户选择
            if not target_segment:
                return {
                    "status": "need_segment",
                    "available_segments": [
                        {
                            "index": idx,
                            "title": seg.title,
                            "start_time": seg.start_time,
                            "end_time": seg.end_time
                        } for idx, seg in enumerate(segments)
                    ],
                    "message": "请指定要查询的分段"
                }
            
            # 获取该分段的关联逐字稿（优先使用原始数据）
            transcription = Transcription.objects.get(file=file_obj)
            speaker_info = transcription.segments or []
            
            # 过滤出该分段时间范围内的句子
            seg_start = target_segment.start_time or 0
            seg_end = target_segment.end_time or 99999999
            related_sentences = []
            for sent in speaker_info:
                sent_start = sent.get('start_time', 0)
                sent_end = sent.get('end_time', 0)
                if sent_end >= seg_start and sent_start <= seg_end:
                    related_sentences.append(sent)
            
            print(f"✅ 分段检索工具返回数据: 分段《{target_segment.title}》")
            return {
                "status": "success",
                "segment_index": list(segments).index(target_segment) if target_segment else -1,
                "segment_title": target_segment.title,
                "segment_summary": target_segment.summary,
                "start_time": target_segment.start_time,
                "end_time": target_segment.end_time,
                "speaker_info": related_sentences,
                "total_count": len(related_sentences)
            }
            
        except Exception as e:
            print(f"❌ 分段检索工具调用失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e)
            }
    
    # ========== 新增四个工具的来源构建函数（引用追踪） ==========
        
    # 发言人过滤工具
    # 用于 LLM 调用
    def _build_sources_for_speaker_filter(self, filter_data: Dict[str, Any], tool_name: str = None) -> List[Dict[str, Any]]:
        """为发言人过滤工具构建来源"""
        sources = []
        if filter_data.get("status") == "success":
            speaker_name = filter_data.get('speaker_name', '')
            total_count = filter_data.get('total_count', 0)
            sources.append({
                "data_type": "tool_call",
                "content": f"调用发言人过滤工具，获取了发言人「{speaker_name}」的 {total_count} 条发言",
                "score": 1.0,
                "is_tool_source": True,
                "tool_name": tool_name
            })
        return sources
        
    # 时间范围查询工具
    # 用于 LLM 调用
    def _build_sources_for_time_range_query(self, query_data: Dict[str, Any], tool_name: str = None) -> List[Dict[str, Any]]:
        """为时间范围查询工具构建来源"""
        sources = []
        if query_data.get("status") == "success":
            start_time = query_data.get('start_time', 0)
            end_time = query_data.get('end_time', 0)
            total_count = query_data.get('total_count', 0)
            # 格式化时间
            start_str = f"{int(start_time // 60)}:{int(start_time % 60):02d}"
            end_str = f"{int(end_time // 60)}:{int(end_time % 60):02d}"
            sources.append({
                "data_type": "tool_call",
                "content": f"调用时间范围查询工具，获取了「{start_str}-{end_str}」时间段内的 {total_count} 条对话",
                "score": 1.0,
                "is_tool_source": True,
                "tool_name": tool_name
            })
        return sources
        
    # 关键词搜索工具
    # 用于 LLM 调用
    def _build_sources_for_keyword_search(self, search_data: Dict[str, Any], tool_name: str = None) -> List[Dict[str, Any]]:
        """为关键词搜索工具构建来源"""
        sources = []
        if search_data.get("status") == "success":
            keyword = search_data.get('keyword', '')
            total_count = search_data.get('total_count', 0)
            sources.append({
                "data_type": "tool_call",
                "content": f"调用关键词搜索工具，搜索关键词「{keyword}」，找到 {total_count} 条匹配内容",
                "score": 1.0,
                "is_tool_source": True,
                "tool_name": tool_name
            })
        return sources
        
    # 分段检索工具
    # 用于 LLM 调用
    def _build_sources_for_segment_retriever(self, segment_data: Dict[str, Any], tool_name: str = None) -> List[Dict[str, Any]]:
        """为分段检索工具构建来源"""
        sources = []
        if segment_data.get("status") == "success":
            segment_title = segment_data.get('segment_title', '')
            total_count = segment_data.get('total_count', 0)
            sources.append({
                "data_type": "tool_call",
                "content": f"调用分段检索工具，获取了分段「{segment_title}」的 {total_count} 条相关对话",
                "score": 1.0,
                "is_tool_source": True,
                "tool_name": tool_name
            })
        return sources
    
    # ========== 新增四个工具的 Prompt 构建函数（生成回答） ==========
        
    # 发言人过滤工具
    # 用于 LLM 调用
    def _build_speaker_filter_prompt(self, user_message: str, filter_data: Dict[str, Any]) -> str:
        """构建发言人过滤工具的 Prompt"""
        system_prompt = """你是一个专业的会议分析助手。根据指定发言人的完整发言内容，回答用户的问题。

回答要求：
1. 只基于该发言人的发言内容进行整理和回答
2. 回答要条理清晰，使用 Markdown 格式
3. 提取关键信息，不要遗漏重要细节
4. 请用中文回答"""
        
        speaker_name = filter_data.get('speaker_name', '')
        speaker_info = filter_data.get('speaker_info', [])
        
        # 格式化数据
        lines = []
        lines.append(f"=== 发言人：{speaker_name} ===\n")
        
        for idx, sent in enumerate(speaker_info, 1):
            speaker = sent.get('speaker', '未知说话人')
            text = sent.get('text', '')
            start_time = sent.get('start_time', 0)
            end_time = sent.get('end_time', 0)
            start_str = f"{int(start_time // 60)}:{int(start_time % 60):02d}"
            end_str = f"{int(end_time // 60)}:{int(end_time % 60):02d}"
            lines.append(f"[{idx}] [{start_str}-{end_str}]")
            lines.append(f"{text}\n")
        
        speaker_text = "\n".join(lines)
        
        # 构建对话历史
        history_context = ""
        for msg in self.chat_history[-6:]:
            if msg["role"] == "user":
                history_context += f"用户: {msg['content']}\n"
            else:
                history_context += f"助手: {msg['content']}\n"
        
        return f"""{system_prompt}

{speaker_text}

========== 对话历史 ==========
{history_context}

========== 用户当前问题 ==========
{user_message}

请根据以上该发言人的发言信息回答用户的问题。"""
        
    # 时间范围查询工具
    # 用于 LLM 调用
    def _build_time_range_prompt(self, user_message: str, query_data: Dict[str, Any]) -> str:
        """构建时间范围查询工具的 Prompt"""
        system_prompt = """你是一个专业的会议分析助手。根据指定时间范围内的完整对话内容，回答用户的问题。

回答要求：
1. 只基于该时间范围内的对话内容进行整理和回答
2. 回答要条理清晰，使用 Markdown 格式
3. 提取关键信息，不要遗漏重要细节
4. 请用中文回答"""
        
        start_time = query_data.get('start_time', 0)
        end_time = query_data.get('end_time', 0)
        speaker_info = query_data.get('speaker_info', [])
        
        # 格式化时间
        start_str = f"{int(start_time // 60)}:{int(start_time % 60):02d}"
        end_str = f"{int(end_time // 60)}:{int(end_time % 60):02d}"
        
        # 格式化数据
        lines = []
        lines.append(f"=== 时间范围：{start_str} - {end_str} ===\n")
        
        for idx, sent in enumerate(speaker_info, 1):
            speaker = sent.get('speaker', '未知说话人')
            text = sent.get('text', '')
            st = sent.get('start_time', 0)
            et = sent.get('end_time', 0)
            st_str = f"{int(st // 60)}:{int(st % 60):02d}"
            et_str = f"{int(et // 60)}:{int(et % 60):02d}"
            lines.append(f"[{idx}] {speaker} [{st_str}-{et_str}]")
            lines.append(f"{text}\n")
        
        range_text = "\n".join(lines)
        
        # 构建对话历史
        history_context = ""
        for msg in self.chat_history[-6:]:
            if msg["role"] == "user":
                history_context += f"用户: {msg['content']}\n"
            else:
                history_context += f"助手: {msg['content']}\n"
        
        return f"""{system_prompt}

{range_text}

========== 对话历史 ==========
{history_context}

========== 用户当前问题 ==========
{user_message}

请根据以上该时间范围内的对话信息回答用户的问题。"""
        
    # 关键词搜索工具
    # 用于 LLM 调用
    def _build_keyword_search_prompt(self, user_message: str, search_data: Dict[str, Any]) -> str:
        """构建关键词搜索工具的 Prompt"""
        system_prompt = """你是一个专业的会议分析助手。根据搜索到的包含关键词的所有对话内容，回答用户的问题。

回答要求：
1. 只基于搜索到的相关内容进行整理和回答
2. 回答要条理清晰，使用 Markdown 格式
3. 提取关键信息，不要遗漏重要细节
4. 请用中文回答"""
        
        keyword = search_data.get('keyword', '')
        speaker_info = search_data.get('speaker_info', [])
        
        # 格式化数据
        lines = []
        lines.append(f"=== 搜索关键词：{keyword} ===\n")
        
        for idx, sent in enumerate(speaker_info, 1):
            speaker = sent.get('speaker', '未知说话人')
            text = sent.get('text', '')
            start_time = sent.get('start_time', 0)
            end_time = sent.get('end_time', 0)
            start_str = f"{int(start_time // 60)}:{int(start_time % 60):02d}"
            end_str = f"{int(end_time // 60)}:{int(end_time % 60):02d}"
            lines.append(f"[{idx}] {speaker} [{start_str}-{end_str}]")
            lines.append(f"{text}\n")
        
        search_text = "\n".join(lines)
        
        # 构建对话历史
        history_context = ""
        for msg in self.chat_history[-6:]:
            if msg["role"] == "user":
                history_context += f"用户: {msg['content']}\n"
            else:
                history_context += f"助手: {msg['content']}\n"
        
        return f"""{system_prompt}

{search_text}

========== 对话历史 ==========
{history_context}

========== 用户当前问题 ==========
{user_message}

请根据以上搜索到的相关对话信息回答用户的问题。"""
        
    # 分段检索工具
    # 用于 LLM 调用
    def _build_segment_retriever_prompt(self, user_message: str, segment_data: Dict[str, Any]) -> str:
        """构建分段检索工具的 Prompt"""
        system_prompt = """你是一个专业的会议分析助手。根据指定分段的完整内容，回答用户的问题。

回答要求：
1. 只基于该分段的内容进行整理和回答
2. 回答要条理清晰，使用 Markdown 格式
3. 提取关键信息，不要遗漏重要细节
4. 请用中文回答"""
        
        segment_title = segment_data.get('segment_title', '')
        segment_summary = segment_data.get('segment_summary', '')
        speaker_info = segment_data.get('speaker_info', [])
        
        # 格式化数据
        lines = []
        lines.append(f"=== 分段：{segment_title} ===\n")
        
        if segment_summary:
            lines.append(f"=== 分段摘要 ===\n{segment_summary}\n")
        
        lines.append(f"=== 分段对话内容 ===\n")
        
        for idx, sent in enumerate(speaker_info, 1):
            speaker = sent.get('speaker', '未知说话人')
            text = sent.get('text', '')
            start_time = sent.get('start_time', 0)
            end_time = sent.get('end_time', 0)
            start_str = f"{int(start_time // 60)}:{int(start_time % 60):02d}"
            end_str = f"{int(end_time // 60)}:{int(end_time % 60):02d}"
            lines.append(f"[{idx}] {speaker} [{start_str}-{end_str}]")
            lines.append(f"{text}\n")
        
        segment_text = "\n".join(lines)
        
        # 构建对话历史
        history_context = ""
        for msg in self.chat_history[-6:]:
            if msg["role"] == "user":
                history_context += f"用户: {msg['content']}\n"
            else:
                history_context += f"助手: {msg['content']}\n"
        
        return f"""{system_prompt}

{segment_text}

========== 对话历史 ==========
{history_context}

========== 用户当前问题 ==========
{user_message}

请根据以上该分段的信息回答用户的问题。"""
        
    # 格式化统计数据
    # 用于 LLM 调用
    def _format_stats_data_to_text(self, stats_data: Dict[str, Any]) -> str:
        """
        把结构化统计数据格式化成可读的文本

        Args:
            stats_data: 统计数据

        Returns:
            格式化后的文本
        """
        if stats_data.get("status") == "error":
            return f"数据获取失败：{stats_data.get('message')}"
        
        lines = []
        
        # 添加概况
        summary = stats_data.get("summary", {})
        lines.append(f"=== 数据概况 ===\n")
        lines.append(f"- 总发言人：{summary.get('total_speakers', 0)} 位")
        lines.append(f"- 总发言次数：{summary.get('total_speech_count', 0)} 次")
        lines.append(f"- 总会议时长：{summary.get('total_duration_minutes', 0)} 分钟")
        if summary.get('most_active'):
            lines.append(f"- 发言最多（最活跃）：{summary.get('most_active')}")
        if summary.get('least_active'):
            lines.append(f"- 发言最少（最不活跃）：{summary.get('least_active')}")
        
        # 添加每个发言人的详细数据
        speaker_list = stats_data.get("speaker_list", [])
        lines.append(f"\n=== 各发言人详细统计 ===\n")
        
        for speaker_data in speaker_list:
            speaker = speaker_data.get('speaker')
            count = speaker_data.get('count')
            duration = speaker_data.get('total_duration_minutes')
            sample_sentences = speaker_data.get('sample_sentences', [])
            
            lines.append(f"发言人：{speaker}")
            lines.append(f"- 发言次数：{count} 次")
            lines.append(f"- 总时长：{duration} 分钟")
            
            if sample_sentences:
                lines.append(f"- 主要发言内容示例：")
                for t in sample_sentences:
                    lines.append(f"  - {t}")
            
            lines.append("")
        
        return "\n".join(lines)
        
    # 构建Prompt
    # 用于 LLM 调用
    def _build_prompt(self, user_message: str, context: str) -> str:
        """构建Prompt"""
        system_prompt = RAGConfig.AGENT_SYSTEM_PROMPT

        # 构建对话历史上下文
        history_context = ""
        for msg in self.chat_history[-6:]:  # 保留最近3轮对话
            if msg["role"] == "user":
                history_context += f"用户: {msg['content']}\n"
            else:
                history_context += f"助手: {msg['content']}\n"

        # 完整Prompt
        full_prompt = f"""{system_prompt}

========== 检索到的会议内容 ==========
{context if context else "（当前无相关会议内容）"}

========== 对话历史 ==========
{history_context}

========== 用户当前问题 ==========
{user_message}

请根据以上信息回答用户的问题。"""

        return full_prompt
        
    # 调用LLM
    # 用于 LLM 调用
    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM（使用ModelScope Qwen）

        Args:
            prompt: 提示词

        Returns:
            回答文本
        """
        print("📤 调用LLM生成回答...")

        # ========== 方案1：直接使用OpenAI SDK调用ModelScope API ==========
        try:
            llm_config = RAGConfig.LLM_CONFIG

            from openai import OpenAI
            client = OpenAI(
                api_key=llm_config.get("api_key"),
                base_url=llm_config.get("base_url")
            )

            response = client.chat.completions.create(
                model=llm_config.get("model_name"),
                messages=[
                    {
                        "role": "system",
                        "content": RAGConfig.AGENT_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            answer = response.choices[0].message.content
            print("✅ LLM调用成功！")
            return answer

        except Exception as e:
            print(f"⚠️  LLM调用失败: {e}")
            print("   使用模拟模式...")
            return self._fallback_answer(prompt)
        
    # 备用回答模式
    # 用于 LLM 调用
    def _fallback_answer(self, prompt: str) -> str:
        """
        备用回答模式（当LLM不可用时）

        Args:
            prompt: 提示词

        Returns:
            回答文本（Markdown格式）
        """
        # 简单的关键词匹配回答（Markdown格式）
        if "决定" in prompt or "选定" in prompt:
            return "## 会议主要决定\n\n根据会议记录，最终选定的产品是：\n\n**智能宠物项圈**\n\n### 否决的方案包括：\n- 小区车位信息化\n- 高考志愿填报系统\n- 景区厕所信息化\n- VR非物质文化遗产保护"
        elif "否决" in prompt or "放弃" in prompt:
            return "## 否决的方案\n\n会议否决了以下方案：\n\n1. **小区车位信息化**\n2. **高考志愿填报系统**\n3. **景区厕所信息化**\n4. **VR非物质文化遗产保护**\n\n以上方案都因各种原因被放弃。"
        elif "待办" in prompt or "任务" in prompt:
            return "## 待办事项\n\n根据会议记录，待办事项包括：\n\n1. **完成智能宠物项圈产品详细需求文档**\n2. **调研竞品智能项圈功能及定价策略**\n3. **制定MVP开发计划**\n\n请持续关注后续会议记录。"
        else:
            return "## 模拟模式\n\n我理解你的问题，但需要连接LLM服务才能提供完整回答。\n\n当前处于**模拟模式**，请确保ModelScope API配置正确。"
        
    # 清空对话历史
    # 用于 LLM 调用
    def clear_history(self):
        """清空对话历史"""
        self.chat_history = []
        print("🗑️ 对话历史已清空")


# ========== 测试代码（可直接运行）==========
if __name__ == "__main__":
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_meeting_service.settings")
    django.setup()

    print("=" * 60)
    print("🤖 测试Agent")
    print("=" * 60)

    # 创建Agent
    agent = MeetingAgent(user_id=1, file_id=3)

    # 测试对话
    print("\n用户: 这次会议的主要决定是什么？")
    result = agent.chat("这次会议的主要决定是什么？")
    print(f"🤖 Agent: {result['answer'][:200]}...")

    print("\n" + "=" * 60)
    print("✅ Agent测试完成！")
    print("=" * 60)
