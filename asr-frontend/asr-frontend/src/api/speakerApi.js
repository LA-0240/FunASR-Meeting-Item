import api from './index';

// Speaker 管理相关 API
export const speakerApi = {
  // 获取 Speaker 列表
  getList: (name = '') => {
    return api.get('/speaker/list', { params: { name } });
  },

  // 创建 Speaker（同时可选上传第一条声纹）
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

  // 更新 Speaker（重命名 + 上传头像）
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

  // 删除 Speaker（级联删除声纹）
  delete: (speakerId) => {
    return api.post('/speaker/delete', { id: speakerId });
  },

  // 给 Speaker 追加声纹
  addVoiceprint: (speakerId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/speaker/${speakerId}/voiceprint/add`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 删除 Speaker 的声纹
  deleteVoiceprint: (speakerId, voiceprintId) => {
    return api.post(`/speaker/${speakerId}/voiceprint/delete/${voiceprintId}`);
  },

  // 更新 Speaker 的声纹
  updateVoiceprint: (speakerId, voiceprintId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/speaker/${speakerId}/voiceprint/update/${voiceprintId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 上传 Speaker 头像
  uploadAvatar: (speakerId, file) => {
    const formData = new FormData();
    formData.append('avatar', file);
    return api.post(`/speaker/avatar/upload/${speakerId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 删除 Speaker 头像
  deleteAvatar: (speakerId) => {
    return api.post(`/speaker/avatar/delete/${speakerId}`);
  },

  // 获取 Speaker 声纹音频（用于播放）
  getVoiceprintAudio: (speakerId, voiceprintId) => {
    return api.get(`/speaker/${speakerId}/voiceprint/audio/${voiceprintId}`, {
      responseType: 'blob'
    });
  }
};
