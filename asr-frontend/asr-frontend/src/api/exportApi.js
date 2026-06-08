/**
 * 文档导出 API 模块
 * ===================
 * 
 * 本模块提供会议文档导出相关的API接口，
 * 主要是Word文档导出功能。
 * 
 * 主要功能：
 * 1. 逐字稿导出为Word文档
 * 2. 自动处理文件下载
 * 
 * 使用方式：
 * import { exportApi } from './api/exportApi';
 * 
 * exportApi.exportToWord(data);
 */

import request from "./index";

/**
 * 文档导出API对象
 * 
 * 包含所有文档导出相关的API方法
 */
export const exportApi = {
  /**
   * 导出Word文档
   * 
   * 将会议内容导出为Word文档并自动下载
   * 
   * @param {Object} data - 导出数据
   * @param {string} data.transcription_text - 文本内容
   * @param {string} data.file_name - 文件名
   * @param {number} [data.file_id] - 文件ID（可选）
   * @returns {Promise<boolean>} 导出成功返回true
   */
  exportToWord: async (data) => {
    try {
      const response = await request({
        url: '/export_transcription_word',
        method: 'POST',
        data: data,
        responseType: 'blob' // 重要！声明返回二进制数据
      });
      
      // 处理下载
      // 注意：如果配置了响应拦截器返回response（当responseType是blob时），直接用response
      // 如果拦截器返回response.data，用response
      const blobData = response.data || response;
      const blob = new Blob([blobData], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // 文件名处理
      const fileName = data.file_name || '文档导出';
      link.download = `${fileName}.docx`;
      
      // 触发下载
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // 释放URL对象
      window.URL.revokeObjectURL(url);
      
      console.log('✅ Word文档导出成功！');
      return true;
    } catch (error) {
      console.error('❌ Word文档导出失败：', error);
      throw error;
    }
  }
};
