import request from "./index";

export const exportApi = {
  /**
   * 导出Word文档
   * @param {Object} data - 导出数据
   * @param {string} data.transcription_text - 文本内容
   * @param {string} data.file_name - 文件名
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