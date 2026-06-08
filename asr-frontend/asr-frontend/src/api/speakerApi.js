/**
 * 说话人管理 API 模块
 * =====================
 * 
 * 本模块提供说话人档案管理相关的API接口，
 * 包括创建、修改、删除说话人，以及声纹和头像管理。
 * 
 * 主要功能：
 * 1. 说话人档案创建、查询、修改、删除
 * 2. 声纹管理（添加、删除、更新）
 * 3. 头像管理（上传、删除）
 * 4. 声纹音频播放
 * 
 * 使用方式：
 * import { speakerApi } from './api/speakerApi';
 * 
 * speakerApi.getList();
 */

import api from './index';

/**
 * 说话人管理API对象
 * 
 * 包含所有说话人档案管理相关的API方法
 */
export const speakerApi = {
  /**
   * 获取说话人列表
   * 
   * 查询系统中的说话人档案，支持按名称搜索
   * 
   * @param {string} [name] - 搜索关键词（可选）
   * @returns {Promise<Array>} 说话人列表
   */
  getList: (name = '') => {
    return api.get('/speaker/list', { params: { name } });
  },

  /**
   * 创建说话人
   * 
   * 创建新的说话人档案，同时可选上传第一条声纹
   * 
   * @param {string} name - 说话人名称
   * @param {File} [file] - 声纹音频文件（可选）
   * @param {boolean} [forceCreate] - 强制创建（默认false）
   * @returns {Promise<Object>} 创建的说话人信息
   */
  add: (name, file = null, forceCreate = false) => {
    const formData = new FormData();
    formData.append('name', name);
    if (forceCreate) {
      formData.append('force_create', 'true');
    }
    if (file) {
      formData.append('file', file);
    }
    return api.post('/speaker/add', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 更新说话人
   * 
   * 修改说话人信息，包括重命名和上传头像
   * 
   * @param {number} speakerId - 说话人ID
   * @param {string} [name] - 新名称（可选）
   * @param {File} [avatar] - 头像文件（可选）
   * @returns {Promise<Object>} 更新后的说话人信息
   */
  update: (speakerId, name = null, avatar = null) => {
    const formData = new FormData();
    formData.append('id', speakerId);
    if (name) {
      formData.append('name', name);
    }
    if (avatar) {
      formData.append('avatar', avatar);
    }
    return api.post('/speaker/update', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 删除说话人
   * 
   * 删除说话人档案，同时级联删除其所有声纹
   * 
   * @param {number} speakerId - 说话人ID
   * @returns {Promise<Object>} 删除响应
   */
  delete: (speakerId) => {
    return api.post('/speaker/delete', { id: speakerId });
  },

  /**
   * 给说话人追加声纹
   * 
   * 为已有说话人添加新的声纹样本
   * 
   * @param {number} speakerId - 说话人ID
   * @param {File} file - 声纹音频文件
   * @returns {Promise<Object>} 新增的声纹信息
   */
  addVoiceprint: (speakerId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/speaker/${speakerId}/voiceprint/add`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 删除说话人的声纹
   * 
   * 删除指定的声纹样本
   * 
   * @param {number} speakerId - 说话人ID
   * @param {number} voiceprintId - 声纹ID
   * @returns {Promise<Object>} 删除响应
   */
  deleteVoiceprint: (speakerId, voiceprintId) => {
    return api.post(`/speaker/${speakerId}/voiceprint/delete/${voiceprintId}`);
  },

  /**
   * 更新说话人的声纹
   * 
   * 替换现有的声纹音频文件
   * 
   * @param {number} speakerId - 说话人ID
   * @param {number} voiceprintId - 声纹ID
   * @param {File} file - 新的声纹音频文件
   * @returns {Promise<Object>} 更新后的声纹信息
   */
  updateVoiceprint: (speakerId, voiceprintId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/speaker/${speakerId}/voiceprint/update/${voiceprintId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 上传说话人头像
   * 
   * 为说话人上传头像图片
   * 
   * @param {number} speakerId - 说话人ID
   * @param {File} file - 头像图片文件
   * @returns {Promise<Object>} 上传响应
   */
  uploadAvatar: (speakerId, file) => {
    const formData = new FormData();
    formData.append('avatar', file);
    return api.post(`/speaker/avatar/upload/${speakerId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 删除说话人头像
   * 
   * 删除已上传的头像
   * 
   * @param {number} speakerId - 说话人ID
   * @returns {Promise<Object>} 删除响应
   */
  deleteAvatar: (speakerId) => {
    return api.post(`/speaker/avatar/delete/${speakerId}`);
  },

  /**
   * 获取说话人声纹音频
   * 
   * 获取声纹样本的音频文件（用于播放）
   * 
   * @param {number} speakerId - 说话人ID
   * @param {number} voiceprintId - 声纹ID
   * @returns {Promise<Blob>} 音频Blob对象
   */
  getVoiceprintAudio: (speakerId, voiceprintId) => {
    return api.get(`/speaker/${speakerId}/voiceprint/audio/${voiceprintId}`, {
      responseType: 'blob'
    });
  }
};
