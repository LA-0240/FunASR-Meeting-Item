import api from './index';

// 会议相关API
export const meetingApi = {
  // 获取逐字稿
  getTranscription: (fileId) => {
    console.log('🔍 [API] 获取逐字稿，fileId:', fileId);
    return api.get(`/transcription/get/${fileId}`);
  },

  // 搜索逐字稿
  searchTranscription: (fileId, keyword) => {
    console.log('🔍 [API] 搜索逐字稿，fileId:', fileId, 'keyword:', keyword);
    return api.post('/transcription/search', { file_id: fileId, keyword });
  },

  // 编辑逐字稿
  editTranscription: (fileId, sentenceIndex, text, speaker) => {
    console.log('✏️ [API] 编辑逐字稿，fileId:', fileId, 'sentenceIndex:', sentenceIndex);
    return api.put('/transcription/edit', {
      file_id: fileId,
      sentence_index: sentenceIndex,
      text,
      speaker
    });
  },

  // 生成逐字稿
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

  // 获取会议纪要
  getSummary: (fileId) => {
    console.log('🔍 [API] 获取会议纪要，fileId:', fileId);
    return api.get('/meeting/summary/get', { params: { file_id: fileId } });
  },

  // 获取会议摘要
  getAbstract: (fileId) => {
    console.log('🔍 [API] 获取会议摘要，fileId:', fileId);
    return api.get('/meeting/abstract/get', { params: { file_id: fileId } });
  },

  // 更新会议纪要
  updateSummary: (fileId, summaryText) => {
    console.log('✏️ [API] 更新会议纪要，fileId:', fileId);
    return api.put('/meeting/summary/update', {
      file_id: fileId,
      summary_text: summaryText
    });
  },

  // 更新会议摘要
  updateAbstract: (fileId, abstractText) => {
    console.log('✏️ [API] 更新会议摘要，fileId:', fileId);
    return api.put('/meeting/abstract/update', {
      file_id: fileId,
      abstract_text: abstractText
    });
  },

  // 生成会议纪要
  generateSummary: (params) => {
    console.log('⚙️ [API] 生成会议纪要，params:', params);
    console.log('📡 [API] 调用链接: http://localhost:8000/generate_summary');
    return api.post('/generate_summary', params);
  },

  // 生成会议摘要
  generateAbstract: (params) => {
    console.log('⚙️ [API] 生成会议摘要，params:', params);
    console.log('📡 [API] 调用链接: http://localhost:8000/meeting_abstract');
    return api.post('/meeting_abstract', params);
  },

  // 获取分段列表
  getSegments: (fileId) => {
    console.log('🔍 [API] 获取分段列表，fileId:', fileId);
    return api.get('/meeting/segments/list', { params: { file_id: fileId } });
  },

  // 生成分段
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

  // 编辑分段
  updateSegment: (segmentId, data) => {
    console.log('✏️ [API] 编辑分段，segmentId:', segmentId, 'data:', data);
    return api.put(`/meeting/segments/update/${segmentId}`, data);
  },

  // 会议分析
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
