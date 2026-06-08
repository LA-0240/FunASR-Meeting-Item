/**
 * 文件管理 API 模块
 * ===================
 * 
 * 本模块提供会议音频文件管理相关的API接口，
 * 包括上传、查询、修改、下载等功能。
 * 
 * 主要功能：
 * 1. 文件上传（支持普通上传和上传+自动转录
 * 2. 文件列表查询
 * 3. 文件信息修改
 * 4. 文件删除
 * 5. 文件下载
 * 
 * 使用方式：
 * import { fileApi } from './api/fileApi';
 * 
 * fileApi.upload(file);
 */

import api from './index';

/**
 * 文件管理API对象
 * 
 * 包含所有文件管理相关的API方法
 */
export const fileApi = {
  /**
   * 文件上传
   * 
   * 上传音频文件到服务器
   * 
   * @param {File} file - 文件对象
   * @returns {Promise<Object>} 上传响应，包含文件信息
   */
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/file/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 文件上传并自动转录
   * 
   * 上传文件后自动触发语音识别和会议转录流程
   * 
   * @param {File} file - 文件对象
   * @param {string} [meeting_type] - 会议类型（可选）
   * @returns {Promise<Object>} 上传和转录响应
   */
  uploadTranscribe: (file, meeting_type) => {
    const formData = new FormData();
    formData.append('file', file);
    if (meeting_type) {
      formData.append('meeting_type', meeting_type);
    }
    return api.post('/file/upload_transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 获取文件列表
   * 
   * 获取当前用户的所有上传文件列表
   * 
   * @param {Object} [params] - 查询参数（可选）
   * @returns {Promise<Array>} 文件列表
   */
  getList: (params = {}) => {
    return api.get('/file/list', { params });
  },

  /**
   * 文件重命名和修改标签
   * 
   * 修改已上传文件的名称和会议类型标签
   * 
   * @param {number} fileId - 文件ID
   * @param {string} newName - 新文件名称
   * @param {string} meetingType - 会议类型
   * @returns {Promise<Object>} 修改响应
   */
  rename: (fileId, newName, meetingType) => {
    return api.post('/file/rename', { file_id: fileId, new_name: newName, meeting_type: meetingType });
  },

  /**
   * 文件删除
   * 
   * 删除指定的文件及其相关数据
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Object>} 删除响应
   */
  delete: (fileId) => {
    return api.post('/file/delete', { file_id: fileId });
  },

  /**
   * 获取文件下载URL
   * 
   * 生成音频文件的完整下载地址
   * 
   * @param {number} fileId - 文件ID
   * @returns {string} 下载URL
   */
  getDownloadUrl: (fileId) => {
    const url = `${api.defaults.baseURL}/file/download/${fileId}`;
    console.log('🌐 [生成下载URL]', url);
    return url;
  }
};
