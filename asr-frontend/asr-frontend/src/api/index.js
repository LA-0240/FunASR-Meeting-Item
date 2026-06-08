/**
 * API 基础配置模块
 * ===================
 * 
 * 本模块负责配置和提供与后端通信的基础axios实例，
 * 包括请求拦截器和响应拦截器的设置，统一处理API通信。
 * 
 * 主要功能：
 * 1. 配置axios实例基础参数（URL、超时、请求头等）
 * 2. 请求拦截器：自动添加认证Token到请求头
 * 3. 响应拦截器：统一处理响应数据，区分Blob和普通数据
 * 
 * 使用方式：
 * import api from './api/index';
 * import { API_BASE_URL } from './api/index';
 * 
 * api.get('/api/some-endpoint');
 */

import axios from 'axios';

/**
 * 后端API基础地址
 * 
 * 开发环境默认为本地地址，生产环境可根据需要修改
 */
export const API_BASE_URL = 'http://localhost:8000';

/**
 * 创建axios实例
 * 
 * 配置了：
 * - baseURL: 后端API基础地址
 * - timeout: 请求超时时间（5分钟，适应语音识别等长时间操作）
 * - headers: 默认Content-Type为JSON
 */
const api = axios.create({
  baseURL: API_BASE_URL, // 后端API地址
  timeout: 300000, // 请求超时时间 (5分钟)
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * 请求拦截器
 * 
 * 在发送请求前自动添加认证Token：
 * 1. 从localStorage中获取token
 * 2. 如果有token，添加到Authorization请求头（Bearer Token格式）
 * 3. 如果没有token，正常发送请求
 */
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

/**
 * 响应拦截器
 * 
 * 统一处理后端响应：
 * 1. 对于Blob类型响应（如音频文件下载），返回完整response对象
 * 2. 对于普通响应，返回response.data（直接获取后端返回的数据）
 * 3. 错误处理：统一输出错误日志，然后reject错误
 */
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
