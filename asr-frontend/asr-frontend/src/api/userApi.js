import api from './index';

// 用户管理相关API
export const userApi = {
  // 用户注册
  register: (userData) => {
    return api.post('/user/register', userData);
  },

  // 用户登录
  login: async (credentials) => {
    const response = await api.post('/user/login', credentials);
    // 登录成功后存储token - 支持多种响应格式
    if (response.token) {
      localStorage.setItem('token', response.token);
    } else if (response.data?.token) {
      localStorage.setItem('token', response.data.token);
    } else if (response.access_token) {
      localStorage.setItem('token', response.access_token);
    }
    return response;
  },

  // 用户退出
  logout: async () => {
    const response = await api.post('/user/logout');
    // 退出成功后清除token
    localStorage.removeItem('token');
    return response;
  },

  // 获取用户信息
  getProfile: () => {
    return api.get('/user/profile');
  }
};