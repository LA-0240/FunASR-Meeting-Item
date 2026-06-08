/**
 * 会议内容管理 API 模块
 * =======================
 * 
 * 本模块提供会议内容管理相关的API接口，
 * 包括逐字稿、会议纪要、分段管理、数据分析等功能。
 * 
 * 主要功能：
 * 1. 逐字稿获取、编辑和搜索
 * 2. 会议纪要和摘要管理
 * 3. 会议分段管理
 * 4. 会议数据分析
 * 
 * 使用方式：
 * import { meetingApi } from './api/meetingApi';
 * 
 * meetingApi.getTranscription(fileId);
 */

import api from './index';

/**
 * 会议内容管理API对象
 * 
 * 包含所有会议内容管理相关的API方法
 */
export const meetingApi = {
  /**
   * 获取逐字稿
   * 
   * 查询指定文件的完整逐字稿
   * 
   * @param {number} fileId - 文件ID
   * @returns {Promise<Object>} 逐字稿数据
   */
  getTranscription: (fileId) => {
    console.log('🔍 [API] 获取逐字稿，fileId:', fileId);
    return api.get(`/transcription/get/${fileId}`);
  },

  /**
   * 搜索逐字稿
   * 
   * 在逐字稿中搜索关键词
   * 
   * @param {number} fileId - 文件ID
   * @param {string} keyword - 搜索关键词
   * @returns {Promise<Array>} 搜索结果
   */
  searchTranscription: (fileId, keyword) => {
    console.log('🔍 [API] 搜索逐字稿，fileId:', fileId, 'keyword:', keyword);
    return api.post('/transcription/search', { file_id: fileId, keyword });
  },

  /**
   * 编辑逐字稿
   * 
   * 修改逐字稿中的句子文本或说话人
   * 
   * @param {number} fileId - 文件ID
   * @param {number} sentenceIndex - 句子索引
   * @param {string} text - 新的文本内容
   * @param {string} speaker - 说话人
   * @returns {Promise<Object>} 更新后的逐字稿
   */
  editTranscription: (fileId, sentenceIndex, text, speaker) => {
    console.log('✏️ [API] 编辑逐字稿，fileId:', fileId, 'sentenceIndex:', sentenceIndex);
    return api.put('/transcription/edit', {
      file_id: fileId,
      sentence_index: sentenceIndex,
      text,
      speaker
    });
  },

  /**
   * 生成逐字稿
   * 
   * 重新生成逐字稿
   * 
   * @param {number} fileId - 文件ID
   * @param {boolean} [forceRegenerate=false] - 是否强制重新生成
   * @returns {Promise<Object>} 逐字稿
   */
  generateTranscription: (fileId, forceRegenerate = false) => {
    console.log('⚙️ [API] 生成逐字稿，fileId:', fileId, 'forceRegenerate:', forceRegenerate);
    console.log('📡 [API] 调用链接: http://localhost:8000/transcription/generate');
    console.log('📋 [API] 参数:', JSON.stringify({
      file_id: fileId,
      force_regenerate: forceRegenerate
    }, null, 2));
    return api.post('/transcription/generate', {
      file_id: fileId,
      force_regenerate: forceRegenerate
    });
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
    console.log('🔍 [API] 获取会议纪要，fileId:', fileId);
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
    console.log('🔍 [API] 获取会议摘要，fileId:', fileId);
    return api.get('/meeting/abstract/get', { params: { file_id: fileId } });
  },

  /**
   * 更新会议纪要
   * 
   * 修改已生成的会议纪要
   * 
   * @param {number} fileId - 文件ID
   * @param {string} summaryText - 新的会议纪要文本
   * @returns {Promise<Object>} 更新后的会议纪要
   */
  updateSummary: (fileId, summaryText) => {
    console.log('✏️ [API] 更新会议纪要，fileId:', fileId);
    return api.put('/meeting/summary/update', {
      file_id: fileId,
      summary_text: summaryText
    });
  },

  /**
   * 更新会议摘要
   * 
   * 修改已生成的会议摘要
   * 
   * @param {number} fileId - 文件ID
   * @param {string} abstractText - 新的会议摘要文本
   * @returns {Promise<Object>} 更新后的会议摘要
   */
  updateAbstract: (fileId, abstractText) => {
    console.log('✏️ [API] 更新会议摘要，fileId:', fileId);
    return api.put('/meeting/abstract/update', {
      file_id: fileId,
      abstract_text: abstractText
    });
  },

  /**
   * 生成会议纪要
   * 
   * 基于逐字稿生成详细的会议纪要
   * 
   * @param {Object} params - 生成参数
   * @returns {Promise<Object>} 会议纪要
   */
  generateSummary: (params) => {
    console.log('⚙️ [API] 生成会议纪要，params:', params);
    console.log('📡 [API] 调用链接: http://localhost:8000/generate_summary');
    return api.post('/generate_summary', params);
  },

  /**
   * 生成会议摘要
   * 
   * 基于逐字稿生成简短的会议摘要
   * 
   * @param {Object} params - 生成参数
   * @returns {Promise<Object>} 会议摘要
   */
  generateAbstract: (params) => {
    console.log('⚙️ [API] 生成会议摘要，params:', params);
    console.log('📡 [API] 调用链接: http://localhost:8000/meeting_abstract');
    return api.post('/meeting_abstract', params);
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
    console.log('🔍 [API] 获取分段列表，fileId:', fileId);
    return api.get('/meeting/segments/list', { params: { file_id: fileId } });
  },

  /**
   * 生成分段
   * 
   * 将会议内容按主题自动分段
   * 
   * @param {number} fileId - 文件ID
   * @param {boolean} [forceUpdate=false] - 是否强制更新
   * @returns {Promise<Array>} 分段列表
   */
  generateSegments: (fileId, forceUpdate = false) => {
    console.log('⚙️ [API] 生成分段，fileId:', fileId, 'forceUpdate:', forceUpdate);
    console.log('📡 [API] 调用链接: http://localhost:8000/meeting/segments/generate');
    console.log('📋 [API] 参数:', JSON.stringify({
      file_id: fileId,
      force_update: forceUpdate
    }, null, 2));
    return api.post('/meeting/segments/generate', {
      file_id: fileId,
      force_update: forceUpdate
    });
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
    console.log('✏️ [API] 编辑分段，segmentId:', segmentId, 'data:', data);
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
  getAnalysis: (fileId, analysisType = 'all', detailLevel = 'basic') => {
    console.log('🔍 [API] 会议分析，fileId:', fileId);
    return api.get(`/meeting/analysis/${fileId}`, {
      params: {
        analysis_type: analysisType,
        detail_level: detailLevel
      }
    });
  }
};
