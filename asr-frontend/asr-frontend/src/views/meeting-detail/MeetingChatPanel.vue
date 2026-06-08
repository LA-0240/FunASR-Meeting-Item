<template>
  <div class="meeting-chat-panel">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <div class="header-title">
        <span class="icon">🤖</span>
        <span>智能会议助手</span>
      </div>
      <div class="header-actions">
        <!-- 索引文件按钮 -->
        <button 
          class="index-btn" 
          @click="handleIndexFile" 
          :disabled="indexing"
          v-if="!isIndexed"
        >
          {{ indexing ? '索引中...' : '索引文件' }}
        </button>
        <!-- 清空历史按钮 -->
        <button 
          class="clear-btn" 
          @click="clearHistory"
          title="清空历史"
        >
          🗑️
        </button>
      </div>
    </div>

    <!-- 索引状态提示 -->
    <div v-if="!isIndexed && !indexing" class="index-hint">
      ⚠️ 当前文件未索引，部分功能可能受限
    </div>
    <!-- 索引成功提示 -->
    <div v-if="showIndexSuccess" class="index-success-hint">
      ✅ 文件索引更新成功！现在可以问我关于最新会议的问题了
    </div>

    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 空状态提示 -->
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <div class="empty-text">
          有问题？问我吧！<br/>
          我能帮你：<br/>
          - 查找会议内容<br/>
          - 总结关键要点<br/>
          - 回答相关问题
        </div>
      </div>
      <!-- 消息列表 -->
      <div 
        v-for="(msg, idx) in messages" 
        :key="idx"
        class="message-item"
        :class="{ 'user-message': msg.role === 'user', 'assistant-message': msg.role === 'assistant' }"
      >
        <div class="message-avatar">
          <span v-if="msg.role === 'user'">👤</span>
          <span v-else>🤖</span>
        </div>
        <div class="message-content">
          <!-- 用户消息 -->
          <div 
            v-if="msg.role === 'user'" 
            class="message-text"
          >{{ msg.content }}</div>
          <!-- 助手消息（支持 Markdown） -->
          <div 
            v-else 
            class="message-text markdown-body"
            v-html="renderMarkdown(msg.content)"
          ></div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
          
          <!-- 来源引用（如果有） -->
          <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
            <div class="sources-label">参考来源：</div>
            <div class="sources-list">
              <div 
                v-for="(src, sIdx) in msg.sources" 
                :key="sIdx" 
                class="source-item"
                :class="{ 'tool-source': src.is_tool_source }"
              >
                <span class="source-type">{{ formatSourceType(src) }}</span>
                <span class="source-text">{{ src.content.slice(0, 80) }}{{ src.content.length > 80 ? '...' : '' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载中提示（打字动画） -->
      <div v-if="loading" class="message-item assistant-message">
        <div class="message-avatar"><span>🤖</span></div>
        <div class="message-content">
          <div class="message-text typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <!-- 文本输入框 -->
        <textarea
          v-model="inputText"
          class="chat-input"
          placeholder="输入你的问题..."
          rows="1"
          @keydown.enter.prevent="handleSend"
          @input="autoResize"
        ></textarea>
        <!-- 发送按钮 -->
        <button 
          class="send-btn" 
          @click="handleSend"
          :disabled="!inputText.trim() || loading"
        >
          发送
        </button>
      </div>
      <div class="input-hint">按 Enter 发送</div>
    </div>
  </div>
</template>

<script>
/**
 * 智能会议助手聊天面板组件
 * 
 * 基于 RAG 技术的会议内容问答系统，支持文件索引、智能对话、来源引用等功能
 * 
 * 功能特点：
 * - 文件索引管理：自动索引或手动触发索引
 * - 智能对话：与会议内容进行自然语言问答
 * - Markdown 渲染：支持富文本回答展示
 * - 来源引用：显示答案的参考来源（逐字稿、分段、工具调用等）
 * - 本地存储：保存聊天历史
 * - 索引状态轮询：异步索引进度监听
 * 
 * @component
 * @example
 * <MeetingChatPanel 
 *   :fileId="currentFileId" 
 *   :userId="currentUserId" 
 * />
 */
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { ragApi } from '../../api/ragApi';
import { marked } from 'marked';

export default {
  name: 'MeetingChatPanel',
  props: {
    /**
     * 会议文件 ID
     */
    fileId: {
      type: [Number, String],
      required: true
    },
    /**
     * 当前用户 ID（用于本地存储区分不同用户）
     */
    userId: {
      type: [Number, String],
      default: null
    }
  },
  setup(props) {
    // ===== 响应式数据 =====
    const messages = ref([]);          // 聊天消息列表
    const inputText = ref('');         // 输入框文本
    const loading = ref(false);        // 发送中状态
    const indexing = ref(false);       // 索引中状态
    const isIndexed = ref(false);      // 是否已索引
    const showIndexSuccess = ref(false); // 显示索引成功提示
    const messagesContainer = ref(null); // 消息容器引用

    // ===== Markdown 渲染 =====
    /**
     * 将 Markdown 文本渲染为 HTML
     * 支持表格、代码块、列表等标准 Markdown 语法
     * 
     * @param {string} content - Markdown 文本
     * @returns {string} 渲染后的 HTML 字符串
     */
    const renderMarkdown = (content) => {
      if (!content) return '';
      try {
        console.log('📝 [Markdown 原始内容]:', content);
        // 显式配置 marked，确保启用表格
        marked.setOptions({
          gfm: true,
          tables: true,
          breaks: true
        });
        const html = marked(content);
        console.log('🟢 [Markdown 渲染 HTML]:', html);
        return html;
      } catch (e) {
        console.error('Markdown 渲染失败:', e);
        return content;
      }
    };

    // ===== 本地存储 =====
    /**
     * 生成本地存储的 key
     * 包含用户 ID 和文件 ID，确保不同用户和文件的历史独立
     * 
     * @returns {string} 本地存储 key
     */
    const getStorageKey = () => {
      return `meeting_chat_${props.userId || 'unknown'}_${props.fileId}`;
    };

    /**
     * 从本地存储加载聊天历史
     * 加载完成后自动滚动到底部
     */
    const loadHistory = () => {
      try {
        const stored = localStorage.getItem(getStorageKey());
        if (stored) {
          messages.value = JSON.parse(stored);
          // 加载完成后滚动到底部
          nextTick(() => {
            scrollToBottom();
          });
        }
      } catch (e) {
        console.error('加载聊天历史失败:', e);
      }
    };

    /**
     * 保存聊天历史到本地存储
     */
    const saveHistory = () => {
      try {
        localStorage.setItem(getStorageKey(), JSON.stringify(messages.value));
      } catch (e) {
        console.error('保存聊天历史失败:', e);
      }
    };

    /**
     * 清空聊天历史
     * 需要用户确认后才会执行
     */
    const clearHistory = () => {
      if (confirm('确定要清空聊天历史吗？')) {
        messages.value = [];
        saveHistory();
      }
    };

    // ===== 索引状态管理 =====
    let statusPollTimer = null; // 轮询计时器
    
    /**
     * 开始轮询索引状态
     * 每1秒检查一次索引状态，直到完成或出错
     * 
     * @param {(string|number)} fileId - 文件 ID
     * @param {boolean} [showMessage=true] - 是否显示系统消息
     */
    const startPollIndexStatus = (fileId, showMessage = true) => {
      // 清除之前的计时器
      if (statusPollTimer) {
        clearInterval(statusPollTimer);
      }
      
      // 每1秒检查一次状态
      statusPollTimer = setInterval(async () => {
        try {
          const res = await ragApi.getStatus(fileId);
          if (res.status === 'success') {
            const indexStatus = res.index_status;
            console.log('📊 索引状态:', indexStatus);
            
            if (indexStatus.status === 'done') {
              // 索引完成
              clearInterval(statusPollTimer);
              statusPollTimer = null;
              indexing.value = false;
              isIndexed.value = true;
              showIndexSuccess.value = true;
              setTimeout(() => {
                showIndexSuccess.value = false;
              }, 3000);
              if (showMessage) {
                addSystemMessage('✅ 文件索引成功！现在可以问我关于会议的问题了。');
              }
            } else if (indexStatus.status === 'error') {
              // 索引出错
              clearInterval(statusPollTimer);
              statusPollTimer = null;
              indexing.value = false;
              if (showMessage) {
                addSystemMessage('❌ 索引失败: ' + (indexStatus.error || '未知错误'));
              }
            }
            // indexing 状态继续等待
          }
        } catch (e) {
          console.error('获取索引状态失败:', e);
        }
      }, 1000);
    };
    
    /**
     * 检查文件并自动索引
     * 每次进入时都重新索引，确保数据最新
     */
    const checkIndexStatus = async () => {
      try {
        const fileIdNum = Number(props.fileId);
        console.log('🔄 MeetingChatPanel - 准备更新索引, fileId:', fileIdNum);
        if (!fileIdNum) {
          console.warn('⚠️ MeetingChatPanel - fileId 无效:', props.fileId);
          return;
        }
        // 每次都重新索引，确保索引是最新的！
        console.log('📚 MeetingChatPanel - 自动索引文件，确保数据最新');
        await handleIndexFile(false); // false 表示不显示多余的系统消息
      } catch (e) {
        console.error('更新索引失败:', e);
      }
    };

    // ===== 索引文件 =====
    let indexPromise = null; // 用于防抖，防止重复请求
    
    /**
     * 触发文件索引（支持异步）
     * 有防抖机制，防止重复请求
     * 
     * @param {boolean} [showMessage=true] - 是否显示系统消息
     * @returns {Promise} 索引请求 Promise
     */
    const handleIndexFile = async (showMessage = true) => {
      if (indexing.value || indexPromise) {
        console.log('⚠️ 索引请求已在进行中，跳过重复请求');
        return indexPromise;
      }
      
      indexing.value = true;
      try {
        const fileIdNum = Number(props.fileId);
        console.log('📚 MeetingChatPanel - 索引文件, fileId:', fileIdNum);
        if (!fileIdNum) {
          if (showMessage) addSystemMessage('❌ 文件ID无效');
          indexing.value = false;
          return;
        }
        
        // 异步索引（立即返回，后台处理）
        indexPromise = ragApi.indexFile(fileIdNum, true); // true = 异步
        const res = await indexPromise;
        
        console.log('✅ 索引响应:', res);
        if (res.status === 'success') {
          if (res.index_status) {
            // 检查是否已在索引中
            if (res.index_status.status === 'indexing') {
              // 已在索引中，开始轮询状态
              console.log('🔄 文件正在索引中，开始轮询状态...');
              if (showMessage) {
                addSystemMessage('🔄 文件正在索引中，请稍候...');
              }
              startPollIndexStatus(fileIdNum, showMessage);
            } else if (res.index_status.status === 'done') {
              // 已经完成了
              isIndexed.value = true;
              indexing.value = false;
              showIndexSuccess.value = true;
              setTimeout(() => {
                showIndexSuccess.value = false;
              }, 3000);
              if (showMessage) {
                addSystemMessage('✅ 文件已索引！现在可以问我关于会议的问题了。');
              }
            } else {
              // 其他状态，开始轮询
              startPollIndexStatus(fileIdNum, showMessage);
            }
          } else {
            // 兼容旧响应（同步索引）
            isIndexed.value = true;
            indexing.value = false;
            showIndexSuccess.value = true;
            setTimeout(() => {
              showIndexSuccess.value = false;
            }, 3000);
            if (showMessage) {
              addSystemMessage('✅ 文件索引成功！现在可以问我关于会议的问题了。');
            }
          }
        } else {
          indexing.value = false;
          if (showMessage) {
            addSystemMessage('❌ ' + (res.detail || '索引失败'));
          }
        }
      } catch (e) {
        indexing.value = false;
        console.error('索引文件失败:', e);
        if (showMessage) {
          if (e.response?.data?.detail) {
            addSystemMessage('❌ ' + e.response.data.detail);
          } else {
            addSystemMessage('❌ 索引失败，请稍后重试');
          }
        }
      } finally {
        indexPromise = null;
      }
    };

    // ===== 消息管理 =====
    /**
     * 添加系统消息到聊天记录
     * 
     * @param {string} content - 消息内容
     */
    const addSystemMessage = (content) => {
      messages.value.push({
        role: 'assistant',
        content,
        timestamp: Date.now(),
        isSystem: true
      });
      saveHistory();
      nextTick(scrollToBottom);
    };

    // ===== 发送消息 =====
    /**
     * 发送用户消息并获取助手回复
     * 包含用户消息、请求后端、处理响应等完整流程
     */
    const handleSend = async () => {
      const text = inputText.value.trim();
      if (!text || loading.value) return;

      const fileIdNum = Number(props.fileId);
      console.log('📤 MeetingChatPanel - 发送消息');
      console.log('   fileId:', fileIdNum);
      console.log('   message:', text);

      if (!fileIdNum) {
        addSystemMessage('❌ 文件ID无效，无法发送消息');
        return;
      }

      // 添加用户消息
      const userMsg = {
        role: 'user',
        content: text,
        timestamp: Date.now()
      };
      messages.value.push(userMsg);
      inputText.value = '';
      loading.value = true;
      saveHistory();
      nextTick(scrollToBottom);

      try {
        // 调用后端 API
        const reqData = {
          file_id: fileIdNum,
          message: text
        };
        console.log('📡 发送请求数据:', reqData);
        const res = await ragApi.chat(reqData);
        console.log('📨 响应数据:', res);

        if (res.status === 'success') {
          const assistantMsg = {
            role: 'assistant',
            content: res.answer,
            sources: res.sources,
            timestamp: Date.now()
          };
          messages.value.push(assistantMsg);
        } else {
          addSystemMessage('❌ ' + (res.detail || '请求失败'));
        }
      } catch (e) {
        console.error('发送消息失败:', e);
        console.error('❌ 错误详情:', {
          message: e.message,
          response: e.response,
          status: e.response?.status,
          data: e.response?.data,
        });
        if (e.response?.data?.detail) {
          addSystemMessage('❌ ' + e.response.data.detail);
        } else if (e.message) {
          addSystemMessage('❌ ' + e.message);
        } else {
          addSystemMessage('❌ 请求失败，请稍后重试');
        }
      } finally {
        loading.value = false;
        saveHistory();
        nextTick(scrollToBottom);
      }
    };

    // ===== 工具函数 =====
    /**
     * 滚动消息容器到底部
     */
    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
    };

    /**
     * 自动调整输入框高度
     * 根据内容自动调整，最大高度 120px
     * 
     * @param {Event} event - 输入事件
     */
    const autoResize = (event) => {
      const textarea = event.target;
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    };

    /**
     * 格式化时间戳为本地时间字符串（仅显示时分）
     * 
     * @param {number} timestamp - 时间戳（毫秒）
     * @returns {string} 格式化的时间字符串，例如 "09:30"
     */
    const formatTime = (timestamp) => {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    };

    /**
     * 格式化秒数为 MM:SS 格式
     * 
     * @param {number} seconds - 秒数
     * @returns {string} 格式化的时间字符串，例如 "01:30"
     */
    const formatSeconds = (seconds) => {
      if (!seconds) return '';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    /**
     * 格式化来源类型显示
     * 根据来源数据类型返回友好的标签
     * 
     * @param {Object} src - 来源对象
     * @returns {string} 格式化的来源类型标签
     */
    const formatSourceType = (src) => {
      const dataType = src.data_type;
      if (dataType === 'tool_call') {
        // 工具调用来源
        if (src.tool_name === 'SPEAKER_STATS') {
          return `[发言统计工具]`;
        } else if (src.tool_name === 'FULL_TRANSCRIPT') {
          return `[完整逐字稿工具]`;
        } else if (src.tool_name === 'SPEAKER_FILTER') {
          return `[发言人过滤工具]`;
        } else if (src.tool_name === 'TIME_RANGE_QUERY') {
          return `[时间范围查询工具]`;
        } else if (src.tool_name === 'KEYWORD_SEARCH') {
          return `[关键词搜索工具]`;
        } else if (src.tool_name === 'SEGMENT_RETRIEVER') {
          return `[分段检索工具]`;
        } else {
          return `[工具调用]`;
        }
      } else if (dataType === 'transcript') {
        const speaker = src.speaker || '未知说话人';
        const start = formatSeconds(src.start_time);
        const end = formatSeconds(src.end_time);
        if (start && end) {
          return `[逐字稿 ${speaker} ${start}-${end}]`;
        } else if (speaker) {
          return `[逐字稿 ${speaker}]`;
        } else {
          return `[逐字稿]`;
        }
      } else if (dataType === 'summary') {
        return `[会议纪要]`;
      } else if (dataType === 'abstract') {
        return `[会议摘要]`;
      } else if (dataType === 'segment') {
        const title = src.title || '';
        const start = formatSeconds(src.start_time);
        const end = formatSeconds(src.end_time);
        if (title && start && end) {
          return `[分段 ${title} ${start}-${end}]`;
        } else if (title) {
          return `[分段 ${title}]`;
        } else {
          return `[分段]`;
        }
      } else if (dataType === 'segment_summary') {
        const title = src.title || '';
        return `[分段摘要 ${title}]`;
      } else if (dataType === 'speaker_stats') {
        const speaker = src.speaker || '';
        if (speaker) {
          return `[发言统计 ${speaker}]`;
        } else {
          return `[发言统计]`;
        }
      } else {
        return `[${dataType}]`;
      }
    };

    // ===== 生命周期钩子 =====
    // 监听 fileId 变化，重新加载历史
    watch(() => props.fileId, () => {
      loadHistory();
      checkIndexStatus();
    }, { immediate: true });
    
    // 组件卸载时清理计时器
    onUnmounted(() => {
      if (statusPollTimer) {
        clearInterval(statusPollTimer);
        statusPollTimer = null;
      }
    });

    // 返回给模板使用
    return {
      messages,
      inputText,
      loading,
      indexing,
      isIndexed,
      showIndexSuccess,
      messagesContainer,
      handleSend,
      handleIndexFile,
      clearHistory,
      autoResize,
      formatTime,
      formatSourceType,
      formatSeconds,
      renderMarkdown
    };
  }
};
</script>

<style scoped>
.meeting-chat-panel {
  background: white;
  border-radius: 0;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.index-btn,
.clear-btn {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: none;
}

.index-btn {
  background: #409eff;
  color: white;
}

.index-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.index-btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.clear-btn {
  background: transparent;
  color: #999;
}

.clear-btn:hover {
  color: #f56c6c;
}

.index-hint {
  padding: 8px 16px;
  background: #fff7e6;
  color: #e6a23c;
  font-size: 12px;
  border-bottom: 1px solid #faecd8;
}

.index-success-hint {
  padding: 8px 16px;
  background: #f0f9ff;
  color: #67c23a;
  font-size: 12px;
  border-bottom: 1px solid #e1f3d8;
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 200px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  line-height: 1.8;
  font-size: 13px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: #ecf5ff;
}

.assistant-message .message-avatar {
  background: #f0f9eb;
}

.message-content {
  flex: 1;
  max-width: 80%;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  background: #f5f7fa;
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.6;
  font-size: 14px;
  color: #333;
  word-wrap: break-word;
}

.user-message .message-text {
  background: #ecf5ff;
  color: #409eff;
}

.message-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
}

.message-sources {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.sources-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-item {
  font-size: 12px;
  color: #666;
}

.source-type {
  color: #409eff;
  font-weight: 500;
  margin-right: 4px;
}

/* 工具调用来源 - 橙色 */
.tool-source {
  background: #fff7e6;
  padding: 4px 8px;
  border-radius: 4px;
  border-left: 3px solid #fa8c16;
}

.tool-source .source-type {
  color: #fa8c16;
}

.typing-indicator {
  display: inline-flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Markdown 样式 */
.message-text.markdown-body {
  line-height: 1.8;
  color: #333;
  font-size: 14px;
}

.message-text.markdown-body h1 {
  font-size: 20px;
  font-weight: 700;
  margin: 16px 0 10px 0;
  padding-bottom: 6px;
  border-bottom: 2px solid #409eff;
  color: #333;
}

.message-text.markdown-body h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 14px 0 8px 0;
  padding-bottom: 4px;
  border-bottom: 1px solid #e5e7eb;
  color: #333;
}

.message-text.markdown-body h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 12px 0 6px 0;
  color: #333;
}

.message-text.markdown-body h4 {
  font-size: 15px;
  font-weight: 600;
  margin: 10px 0 5px 0;
  color: #333;
}

.message-text.markdown-body p {
  margin: 8px 0;
  color: #4b5563;
}

.message-text.markdown-body ul, 
.message-text.markdown-body ol {
  padding-left: 24px;
  margin: 8px 0;
}

.message-text.markdown-body ul {
  list-style-type: disc;
}

.message-text.markdown-body ol {
  list-style-type: decimal;
}

.message-text.markdown-body li {
  margin: 4px 0;
  color: #4b5563;
  list-style-position: outside;
}

.message-text.markdown-body code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #409eff;
}

.message-text.markdown-body pre {
  background: #1f2937;
  color: #e5e7eb;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 10px 0;
}

.message-text.markdown-body pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}

.message-text.markdown-body blockquote {
  border-left: 4px solid #409eff;
  padding-left: 12px;
  margin: 10px 0;
  color: #6b7280;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 4px;
}

.message-text.markdown-body strong {
  color: #111827;
  font-weight: 600;
}

.message-text.markdown-body em {
  color: #4b5563;
  font-style: italic;
}

.message-text.markdown-body a {
  color: #409eff;
  text-decoration: underline;
}

.message-text.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}

.message-text.markdown-body th,
.message-text.markdown-body td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

.message-text.markdown-body th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.message-text.markdown-body tr:nth-child(even) {
  background: #f9fafb;
}

.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #eee;
  background: #fafafa;
  border-radius: 0 0 8px 8px;
}

.input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  resize: none;
  min-height: 38px;
  max-height: 120px;
  line-height: 1.5;
}

.chat-input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.send-btn {
  padding: 10px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.send-btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.input-hint {
  font-size: 11px;
  color: #c0c4cc;
  text-align: right;
  margin-top: 6px;
}

</style>

<!-- Markdown 专用样式（非 scoped） - 给 v-html 渲染的内容用 -->
<style>
.message-text.markdown-body table {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 12px 0 !important;
  font-size: 13px !important;
}

.message-text.markdown-body th,
.message-text.markdown-body td {
  border: 1px solid #e5e7eb !important;
  padding: 8px 12px !important;
  text-align: left !important;
}

.message-text.markdown-body th {
  background: #f9fafb !important;
  font-weight: 600 !important;
  color: #374151 !important;
}

.message-text.markdown-body tr:nth-child(even) {
  background: #f9fafb !important;
}

.message-text.markdown-body ul,
.message-text.markdown-body ol {
  padding-left: 24px !important;
  margin: 8px 0 !important;
  list-style-position: outside !important;
}

.message-text.markdown-body ul {
  list-style-type: disc !important;
}

.message-text.markdown-body ol {
  list-style-type: decimal !important;
}
</style>
