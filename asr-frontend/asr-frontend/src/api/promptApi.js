/**
 * Prompt模板管理 API 模块
 * ===========================
 * 
 * 本模块提供会议Prompt模板管理相关的API接口，
 * 包括模板的增删改查和复制功能。
 * 
 * 主要功能：
 * 1. Prompt模板列表获取
 * 2. 模板创建、更新和删除
 * 3. 模板复制
 * 
 * 使用方式：
 * import { promptApi } from './api/promptApi';
 * 
 * promptApi.getList();
 */

import api from './index';

/**
 * Prompt模板管理API对象
 * 
 * 包含所有Prompt模板管理相关的API方法
 */
export const promptApi = {
  /**
   * 获取模板列表
   * 
   * 获取当前用户的所有Prompt模板
   * 
   * @returns {Promise<Array>} 模板列表
   */
  getList: () => {
    console.log('📞 [API] 调用 /prompt/list 获取模板列表');
    return api.get('/prompt/list');
  },

  /**
   * 添加模板
   * 
   * 创建新的Prompt模板
   * 
   * @param {Object} data - 模板数据
   * @param {string} data.name - 模板名称
   * @param {string} data.content - 模板内容
   * @param {string} [data.description] - 模板描述（可选）
   * @returns {Promise<Object>} 创建的模板
   */
  add: (data) => {
    return api.post('/prompt/add', data);
  },

  /**
   * 更新模板
   * 
   * 修改已有的Prompt模板
   * 
   * @param {number} promptId - 模板ID
   * @param {Object} data - 更新的模板数据
   * @returns {Promise<Object>} 更新后的模板
   */
  update: (promptId, data) => {
    return api.put(`/prompt/update/${promptId}`, data);
  },

  /**
   * 删除模板
   * 
   * 删除指定的Prompt模板
   * 
   * @param {number} promptId - 模板ID
   * @returns {Promise<Object>} 删除响应
   */
  delete: (promptId) => {
    return api.delete(`/prompt/delete/${promptId}`);
  },

  /**
   * 复制模板
   * 
   * 复制已有的Prompt模板为新模板
   * 
   * @param {number} promptId - 要复制的模板ID
   * @returns {Promise<Object>} 新创建的模板
   */
  copy: (promptId) => {
    return api.post(`/prompt/copy/${promptId}`);
  }
};
