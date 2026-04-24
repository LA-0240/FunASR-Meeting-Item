import api from './index';

// ASR相关API
export const asrApi = {
  // 健康检查
  healthCheck: () => {
    return api.get('');
  },
  // 语音转文字
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

  // 视频ASR转录
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

  // 生成会议纪要
  generateSummary: (data) => {
    return api.post('/generate_summary', data);
  },

  // 生成会议摘要
  generateAbstract: (data) => {
    return api.post('/meeting_abstract', data);
  },

  // 更新会议纪要
  updateSummary: (data) => {
    return api.post('/meeting/summary/update', data);
  },

  // 更新会议摘要
  updateAbstract: (data) => {
    return api.post('/meeting/abstract/update', data);
  },

  // 获取会议纪要
  getSummary: (fileId) => {
    return api.get('/meeting/summary/get', { params: { file_id: fileId } });
  },

  // 获取会议摘要
  getAbstract: (fileId) => {
    return api.get('/meeting/abstract/get', { params: { file_id: fileId } });
  },

  // 生成分段
  generateSegments: (data) => {
    return api.post('/meeting/segments/generate', data);
  },

  // 获取分段列表
  getSegments: (fileId) => {
    return api.get('/meeting/segments/list', { params: { file_id: fileId } });
  },

  // 编辑分段
  updateSegment: (segmentId, data) => {
    return api.put(`/meeting/segments/update/${segmentId}`, data);
  },

  // 会议分析
  getMeetingAnalysis: (fileId, analysisType = 'all', detailLevel = 'basic') => {
    return api.get(`/meeting/analysis/${fileId}`, {
      params: { analysis_type: analysisType, detail_level: detailLevel }
    });
  },

  // 逐字稿搜索
  searchTranscription: (keyword) => {
    return api.get('/transcription/search', { params: { keyword } });
  },

  // 获取逐字稿
  getTranscription: (fileId) => {
    return api.get(`/transcription/get/${fileId}`);
  },

  // 编辑逐字稿
  editTranscription: (data) => {
    return api.post('/transcription/edit', data);
  },

  // 生成逐字稿
  generateTranscription: (data) => {
    return api.post('/transcription/generate', data);
  },

  // 导出转录文本为Word
  exportTranscriptionWord: (fileId) => {
    return api.get('/export_transcription_word', { 
      params: { file_id: fileId },
      responseType: 'blob'
    });
  },

  // 导出会议纪要为Word
  exportSummaryWord: (fileId) => {
    return api.get('/export_summary_word', { 
      params: { file_id: fileId },
      responseType: 'blob'
    });
  },

  // 导出会议摘要为Word
  exportAbstractWord: (fileId) => {
    return api.get('/export_abstract_word', { 
      params: { file_id: fileId },
      responseType: 'blob'
    });
  }
};