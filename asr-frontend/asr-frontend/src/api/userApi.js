import api from './index';
import axios from 'axios';
import { API_BASE_URL } from './index';

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
    // 保存用户信息和管理员状态
    if (response.username) {
      localStorage.setItem('username', response.username);
    }
    if (response.is_staff !== undefined) {
      localStorage.setItem('is_staff', response.is_staff);
    }
    if (response.is_superuser !== undefined) {
      localStorage.setItem('is_superuser', response.is_superuser);
    }
    // 保存完整用户信息
    if (response.user_id !== undefined) {
      const userData = {
        user_id: response.user_id,
        username: response.username,
        email: response.email,
        created_at: response.created_at,
        avatar_url: response.avatar_url
      };
      localStorage.setItem('userInfo', JSON.stringify(userData));
    }
    return response;
  },

  // 用户退出
  logout: async () => {
    const response = await api.post('/user/logout');
    // 退出成功后清除所有用户信息
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('is_staff');
    localStorage.removeItem('is_superuser');
    localStorage.removeItem('userInfo');
    return response;
  },

  // 获取用户信息
  getProfile: () => {
    return api.get('/user/profile');
  },

  // 更新用户信息
  updateProfile: (userData) => {
    return api.put('/user/profile', userData);
  },

  // 上传头像
  uploadAvatar: async (avatarFile) => {
    const formData = new FormData();
    formData.append('avatar', avatarFile);
    
    const token = localStorage.getItem('token');
    const response = await axios.post(`${API_BASE_URL}/user/avatar/upload`, formData, {
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  },

  // 删除头像
  deleteAvatar: () => {
    return api.delete('/user/avatar/delete');
  }
};