/**
 * 用户管理 API 模块
 * ===================
 * 
 * 本模块提供用户账户管理相关的API接口，
 * 包括注册、登录、个人资料管理、头像管理等功能。
 * 
 * 主要功能：
 * 1. 用户注册和登录认证
 * 2. 用户登录状态维护（Token管理）
 * 3. 个人资料查询和更新
 * 4. 用户头像上传和删除
 * 
 * 使用方式：
 * import { userApi } from './api/userApi';
 * 
 * userApi.login({ username, password });
 */

import api from './index';
import axios from 'axios';
import { API_BASE_URL } from './index';

/**
 * 用户管理API对象
 * 
 * 包含所有用户账户相关的API方法
 */
export const userApi = {
  /**
   * 用户注册
   * 
   * 创建新的用户账户
   * 
   * @param {Object} userData - 用户注册数据
   * @param {string} userData.username - 用户名
   * @param {string} userData.password - 密码
   * @param {string} userData.email - 邮箱地址
   * @returns {Promise<Object>} 注册响应
   */
  register: (userData) => {
    return api.post('/user/register', userData);
  },

  /**
   * 用户登录
   * 
   * 用户登录认证，成功后自动保存Token和用户信息到localStorage
   * 支持多种后端响应格式（token、data.token、access_token等）
   * 
   * @param {Object} credentials - 用户登录凭证
   * @param {string} credentials.username - 用户名
   * @param {string} credentials.password - 密码
   * @returns {Promise<Object>} 登录响应
   */
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

  /**
   * 用户退出登录
   * 
   * 清除本地存储的所有用户信息和Token，
   * 并调用后端登出接口
   * 
   * @returns {Promise<Object>} 登出响应
   */
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

  /**
   * 获取用户个人资料
   * 
   * 获取当前登录用户的详细信息
   * 
   * @returns {Promise<Object>} 用户资料对象
   */
  getProfile: () => {
    return api.get('/user/profile');
  },

  /**
   * 更新用户个人资料
   * 
   * 修改当前登录用户的信息
   * 
   * @param {Object} userData - 更新的用户数据
   * @param {string} [userData.username] - 新用户名
   * @param {string} [userData.email] - 新邮箱
   * @returns {Promise<Object>} 更新后的用户资料
   */
  updateProfile: (userData) => {
    return api.put('/user/profile', userData);
  },

  /**
   * 上传用户头像
   * 
   * 使用FormData上传用户头像文件
   * 
   * @param {File} avatarFile - 头像文件对象
   * @returns {Promise<Object>} 上传响应（包含新头像URL）
   */
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

  /**
   * 删除用户头像
   * 
   * 删除当前用户已上传的头像
   * 
   * @returns {Promise<Object>} 删除响应
   */
  deleteAvatar: () => {
    return api.delete('/user/avatar/delete');
  }
};
