import api from './index';

// 声纹管理相关API
export const voiceprintApi = {
  // 添加声纹
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

  // 获取声纹列表
  getList: (name = '') => {
    return api.get('/voiceprint/list', { params: { name } });
  },

  // 声纹重命名
  rename: (voiceprintId, newName) => {
    return api.post('/voiceprint/rename', { id: voiceprintId, new_name: newName });
  },

  // 声纹删除
  delete: (voiceprintId) => {
    return api.post('/voiceprint/delete', { id: voiceprintId });
  },

  // 获取声纹音频文件
  getAudio: (voiceprintId) => {
    return api.get(`/voiceprint/audio/${voiceprintId}`, {
      responseType: 'blob' // 重要：设置响应类型为blob，以便前端可以播放音频
    });
  }
};