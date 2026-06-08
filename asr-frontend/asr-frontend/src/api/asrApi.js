/**
 * 语音识别 API 模块
 * ===================
 * 
 * 本模块提供语音识别和会议分析相关的API接口，
 * 包括音频转录、会议摘要、分段管理、数据导出等功能。
 * 
 * 主要功能：
 * 1. 音频/视频语音识别
 * 2. 会议纪要和摘要生成
 * 3. 会议分段管理
 * 4. 会议数据分析
 * 5. 数据导出
 * 
 * 使用方式：
 * import { asrApi } from './api/asrApi';
 * 
 * asrApi.transcribe(file);
 */

import api from './index';

/**
 * 语音识别API对象
 * 
 * 包含所有语音识别和会议分析相关的API方法
 */
export const asrApi = {
  /**
   * 健康检查
   * 
   * 检查后端服务是否正常运行
   * 
   * @returns {Promise<Object>} 服务状态
   */
  healthCheck: () => {
    return api.get('');
  },

  /**
   * 语音转文字
   * 
   * 对音频文件进行语音识别，生成逐字稿
   * 
   * @param {File} file - 音频文件
   * @param {number} [batchSize=300] - 批次大小（秒）
   * @param {string} [hotword] - 热词（可选，辅助识别专有名词）
   * @returns {Promise<Object>} 转录结果
   */
  transcribe: (file, batchSize = 300, hotword = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('batch_size_s', batchSize);
    if (hotword) {
      formData.append('hotword', hotword);
    }
    return api.post('/asr', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 视频ASR转录
   * 
   * 对视频文件进行语音识别（自动提取音频）
   * 
   * @param {File} file - 视频文件
   * @param {number} [batchSize=300] - 批次大小（秒）
   * @param {string} [hotword] - 热词（可选）
   * @returns {Promise<Object>} 转录结果
   */
  videoTranscribe: (file, batchSize = 300, hotword = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('batch_size_s', batchSize);
    if (hotword) {
      formData.append('hotword', hotword);
    }
    return api.post('/video_asr', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 生成会议纪要
   * 
   * 基于逐字稿生成详细的会议纪要
   * 
   * @param {Object} data - 会议数据
   * @returns {Promise<Object>} 会议纪要
   */
  generateSummary: (data) => {
    return api.post('/generate_summary', data);
  },

  /**
   * 生成会议摘要
   * 
   * 基于逐字稿生成简短的会议摘要
   * 
   * @param {Object} data - 会议数据
   * @returns {Promise<Object>} 会议摘要
   */
  generateAbstract: (data) => {
    return api.post('/meeting_abstract', data);
  },

  /**
   * 更新会议纪要
   * 
   * 修改已生成的会议纪要
   * 
   * @param {Object} data - 更新的会议纪要数据
   * @returns {Promise<Object>} 更新后的会议纪要
   */
  updateSummary: (data) => {
    return api.post('/meeting/summary/update', data);
  },

  /**
   * 更新会议摘要
   * 
   * 修改已生成的会议摘要
   * 
   * @param {Object} data - 更新的会议摘要数据
   * @returns {Promise<Object>} 更新后的会议摘要
   */
  updateAbstract: (data) => {
    return api.post('/meeting/abstract/update', data);
  },

  /**
   * 获取会议纪要
   * 
   * 查询指定文件的会议纪要
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Object>} 会议纪要
   */
  getSummary: (fileId) => {
    return api.get('/meeting/summary/get', { params: { file_id: fileId } });
  },

  /**
   * 获取会议摘要
   * 
   * 查询指定文件的会议摘要
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Object>} 会议摘要
   */
  getAbstract: (fileId) => {
    return api.get('/meeting/abstract/get', { params: { file_id: fileId } });
  },

  /**
   * 生成分段
   * 
   * 将会议内容按主题自动分段
   * 
   * @param {Object} data - 会议数据
   * @returns {Promise<Array>} 分段列表
   */
  generateSegments: (data) => {
    return api.post('/meeting/segments/generate', data);
  },

  /**
   * 获取分段列表
   * 
   * 查询指定文件的会议分段
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Array>} 分段列表
   */
  getSegments: (fileId) => {
    return api.get('/meeting/segments/list', { params: { file_id: fileId } });
  },

  /**
   * 编辑分段
   * 
   * 修改会议分段信息
   * 
   * @param {number} segmentId - 分段ID
   * @param {Object} data - 更新的分段数据
   * @returns {Promise<Object>} 更新后的分段
   */
  updateSegment: (segmentId, data) => {
    return api.put(`/meeting/segments/update/${segmentId}`, data);
  },

  /**
   * 会议分析
   * 
   * 获取会议的多维度分析数据
   * 
   * @param {number} fileId - 文件ID
   * @param {string} [analysisType='all'] - 分析类型
   * @param {string} [detailLevel='basic'] - 详细级别
   * @returns {Promise<Object>} 分析结果
   */
  getMeetingAnalysis: (fileId, analysisType = 'all', detailLevel = 'basic') => {
    return api.get(`/meeting/analysis/${fileId}`, {
      params: { analysis_type: analysisType, detail_level: detailLevel }
    });
  },

  /**
   * 逐字稿搜索
   * 
   * 在逐字稿中搜索关键词
   * 
   * @param {string} keyword - 搜索关键词
   * @returns {Promise<Array>} 搜索结果
   */
  searchTranscription: (keyword) => {
    return api.get('/transcription/search', { params: { keyword } });
  },

  /**
   * 获取逐字稿
   * 
   * 查询指定文件的完整逐字稿
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Object>} 逐字稿数据
   */
  getTranscription: (fileId) => {
    return api.get(`/transcription/get/${fileId}`);
  },

  /**
   * 编辑逐字稿
   * 
   * 修改逐字稿内容
   * 
   * @param {Object} data - 更新的逐字稿数据
   * @returns {Promise<Object>} 更新后的逐字稿
   */
  editTranscription: (data) => {
    return api.post('/transcription/edit', data);
  },

  /**
   * 生成逐字稿
   * 
   * 重新生成逐字稿
   * 
   * @param {Object} data - 会议数据
   * @returns {Promise<Object>} 逐字稿
   */
  generateTranscription: (data) => {
    return api.post('/transcription/generate', data);
  },

  /**
   * 导出转录文本为Word
   * 
   * 将逐字稿导出为Word文档
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Blob>} Word文档Blob
   */
  exportTranscriptionWord: (fileId) => {
    return api.get('/export_transcription_word', { 
      params: { file_id: fileId },
      responseType: 'blob'
    });
  },

  /**
   * 导出会议纪要为Word
   * 
   * 将会议纪要导出为Word文档
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Blob>} Word文档Blob
   */
  exportSummaryWord: (fileId) => {
    return api.get('/export_summary_word', { 
      params: { file_id: fileId },
      responseType: 'blob'
    });
  },

  /**
   * 导出会议摘要为Word
   * 
   * 将会议摘要导出为Word文档
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Blob>} Word文档Blob
   */
  exportAbstractWord: (fileId) => {
    return api.get('/export_abstract_word', { 
      params: { file_id: fileId },
      responseType: 'blob'
    });
  }
};
