import axios from 'axios';

// API 基础 URL
export const API_BASE_URL = 'http://localhost:8000';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL, // 后端API地址
  timeout: 300000, // 请求超时时间 (5分钟)
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从本地存储获取token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 对于音频请求，返回完整的响应对象，因为我们需要获取Blob数据
    if (response.config.responseType === 'blob') {
      return response;
    }
    // 其他请求返回response.data
    return response.data;
  },
  error => {
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

export default api;