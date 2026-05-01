import api from './index';

// 文件管理相关API
export const fileApi = {
  // 文件上传
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/file/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 文件上传并自动转录
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

  // 获取文件列表
  getList: (params = {}) => {
    return api.get('/file/list', { params });
  },

  // 文件重命名和修改标签
  rename: (fileId, newName, meetingType) => {
    return api.post('/file/rename', { file_id: fileId, new_name: newName, meeting_type: meetingType });
  },

  // 文件删除
  delete: (fileId) => {
    return api.post('/file/delete', { file_id: fileId });
  },

  // 文件下载
  getDownloadUrl: (fileId) => {
    const url = `${api.defaults.baseURL}/file/download/${fileId}`;
    console.log('🌐 [生成下载URL]', url);
    return url;
  }
};