/**
 * 智能检索问答 API 模块
 * =========================
 * 
 * 本模块提供RAG（检索增强生成）相关的API接口，
 * 包括会议文件索引、智能对话、检索测试等功能。
 * 
 * 主要功能：
 * 1. 会议文件向量化索引
 * 2. 基于会议内容的智能对话
 * 3. 索引状态查询
 * 4. 检索功能测试
 * 
 * 使用方式：
 * import { ragApi } from './api/ragApi';
 * 
 * ragApi.chat(fileId, message);
 */

import api from './index';

/**
 * 智能检索问答API对象
 * 
 * 包含所有RAG功能相关的API方法
 */
export const ragApi = {
    /**
     * 发送聊天消息
     * 
     * 与会议智能助手对话，支持工具调用和RAG检索
     * 
     * @param {number|Object} fileId - 文件ID 或者包含 file_id 和 message 的对象
     * @param {string} message - 用户消息（可选，如果第一个参数是对象）
     * @param {string} sessionId - 会话ID（可选，用于维持多轮对话）
     * @returns {Promise<Object>} AI回复，包含answer、sources、thinking等字段
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
     * 
     * 将会议文件的逐字稿、摘要等内容向量化并存储到向量数据库
     * 
     * @param {number} fileId - 文件ID
     * @param {boolean} async - 是否异步执行，默认为true（异步不阻塞）
     * @returns {Promise<Object>} 索引任务状态
     */
    indexFile(fileId, async = true) {
        return api.post('/rag/index', { file_id: fileId, async });
    },

    /**
     * 获取索引状态
     * 
     * 查询文件索引进度或全局索引状态
     * 
     * @param {number} fileId - 文件ID（可选，不传则查询全局状态）
     * @returns {Promise<Object>} 索引状态信息
     */
    getStatus(fileId = null) {
        const params = fileId ? { file_id: fileId } : {};
        return api.get('/rag/status', { params });
    },

    /**
     * 获取索引状态（别名，用于兼容）
     * 
     * 同getStatus，保持API接口兼容性
     * 
     * @param {number} fileId - 文件ID（可选）
     * @returns {Promise<Object>} 索引状态信息
     */
    getIndexStatus(fileId = null) {
        return this.getStatus(fileId);
    },

    /**
     * 测试检索（可选）
     * 
     * 直接测试检索功能，用于调试和验证索引效果
     * 
     * @param {number} fileId - 文件ID
     * @param {string} query - 查询文本
     * @returns {Promise<Array>} 检索结果列表
     */
    testRetrieve(fileId, query) {
        return api.post('/rag/test', { file_id: fileId, query });
    }
};
