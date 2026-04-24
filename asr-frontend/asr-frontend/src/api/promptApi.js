import api from './index';

// Prompt模板管理相关API
export const promptApi = {
  // 获取模板列表
  getList: () => {
    console.log('📞 [API] 调用 /prompt/list 获取模板列表');
    return api.get('/prompt/list');
  },

  // 添加模板
  add: (data) => {
    return api.post('/prompt/add', data);
  },

  // 更新模板
  update: (promptId, data) => {
    return api.put(`/prompt/update/${promptId}`, data);
  },

  // 删除模板
  delete: (promptId) => {
    return api.delete(`/prompt/delete/${promptId}`);
  },

  // 复制模板
  copy: (promptId) => {
    return api.post(`/prompt/copy/${promptId}`);
  }
};