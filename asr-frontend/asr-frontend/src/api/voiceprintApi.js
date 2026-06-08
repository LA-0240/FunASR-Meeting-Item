/**
 * 声纹管理 API 模块
 * ====================
 * 
 * 本模块提供独立声纹样本管理相关的API接口，
 * 包括声纹的添加、查询、修改和删除。
 * 
 * 主要功能：
 * 1. 声纹样本创建和删除
 * 2. 声纹查询和搜索
 * 3. 声纹重命名
 * 4. 声纹音频和头像管理
 * 
 * 使用方式：
 * import { voiceprintApi } from './api/voiceprintApi';
 * 
 * voiceprintApi.getList();
 */

import api from './index';

/**
 * 声纹管理API对象
 * 
 * 包含所有声纹样本管理相关的API方法
 */
export const voiceprintApi = {
  /**
   * 添加声纹
   * 
   * 创建新的独立声纹样本
   * 
   * @param {File} file - 声纹音频文件
   * @param {string} name - 声纹名称
   * @returns {Promise<Object>} 创建的声纹信息
   */
  add: (file, name) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    return api.post('/voiceprint/add', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 获取声纹列表
   * 
   * 查询所有独立声纹样本，支持按名称搜索
   * 
   * @param {string} [name] - 搜索关键词（可选）
   * @returns {Promise<Array>} 声纹列表
   */
  getList: (name = '') => {
    return api.get('/voiceprint/list', { params: { name } });
  },

  /**
   * 声纹重命名
   * 
   * 修改声纹样本的名称
   * 
   * @param {number} voiceprintId - 声纹ID
   * @param {string} newName - 新名称
   * @returns {Promise<Object>} 更新后的声纹信息
   */
  rename: (voiceprintId, newName) => {
    return api.post('/voiceprint/rename', { id: voiceprintId, new_name: newName });
  },

  /**
   * 声纹删除
   * 
   * 删除指定的声纹样本
   * 
   * @param {number} voiceprintId - 声纹ID
   * @returns {Promise<Object>} 删除响应
   */
  delete: (voiceprintId) => {
    return api.post('/voiceprint/delete', { id: voiceprintId });
  },

  /**
   * 获取声纹音频文件
   * 
   * 获取声纹样本的音频文件（用于播放）
   * 
   * @param {number} voiceprintId - 声纹ID
   * @returns {Promise<Blob>} 音频Blob对象
   */
  getAudio: (voiceprintId) => {
    return api.get(`/voiceprint/audio/${voiceprintId}`, {
      responseType: 'blob' // 重要：设置响应类型为blob，以便前端可以播放音频
    });
  },

  /**
   * 声纹头像上传
   * 
   * 为声纹样本上传头像图片
   * 
   * @param {number} voiceprintId - 声纹ID
   * @param {File} file - 头像图片文件
   * @returns {Promise<Object>} 上传响应
   */
  uploadAvatar: (voiceprintId, file) => {
    const formData = new FormData();
    formData.append('avatar', file);
    return api.post(`/voiceprint/avatar/upload/${voiceprintId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 声纹头像删除
   * 
   * 删除已上传的声纹头像
   * 
   * @param {number} voiceprintId - 声纹ID
   * @returns {Promise<Object>} 删除响应
   */
  deleteAvatar: (voiceprintId) => {
    return api.post(`/voiceprint/avatar/delete/${voiceprintId}`);
  }
};
