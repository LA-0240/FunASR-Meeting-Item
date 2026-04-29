import api from './index';

// RAG 相关 API
export const ragApi = {
    /**
     * 发送聊天消息
     * @param {number|Object} fileId - 文件ID 或者包含 file_id 和 message 的对象
     * @param {string} message - 用户消息（可选，如果第一个参数是对象）
     * @param {string} sessionId - 会话ID（可选）
     */
    chat(fileId, message, sessionId = null) {
        let data;
        // 支持两种调用方式
        if (typeof fileId === 'object' && fileId !== null) {
            data = fileId;
        } else {
            data = {
                file_id: fileId,
                message: message
            };
            if (sessionId) {
                data.session_id = sessionId;
            }
        }
        console.log('📡 ragApi.chat 发送数据:', data);
        return api.post('/rag/chat', data);
    },

    /**
     * 索引会议文件
     * @param {number} fileId - 文件ID
     * @param {boolean} async - 是否异步执行，默认为true
     */
    indexFile(fileId, async = true) {
        return api.post('/rag/index', { file_id: fileId, async });
    },

    /**
     * 获取索引状态
     * @param {number} fileId - 文件ID（可选）
     */
    getStatus(fileId = null) {
        const params = fileId ? { file_id: fileId } : {};
        return api.get('/rag/status', { params });
    },

    /**
     * 获取索引状态（别名，用于兼容）
     * @param {number} fileId - 文件ID（可选）
     */
    getIndexStatus(fileId = null) {
        return this.getStatus(fileId);
    },

    /**
     * 测试检索（可选）
     * @param {number} fileId - 文件ID
     * @param {string} query - 查询文本
     */
    testRetrieve(fileId, query) {
        return api.post('/rag/test', { file_id: fileId, query });
    }
};
