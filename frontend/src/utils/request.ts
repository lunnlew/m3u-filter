import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { App } from 'antd';
import { ApiResponse } from '@/types/api';

const getBaseURL = () => {
  // 判断是否在 Tauri 环境中运行
  if (window.__TAURI_INTERNALS__) {
    return 'http://localhost:3232/api';
  }
  return '/api';
};

const _request = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
});

// 请求拦截器
_request.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
_request.interceptors.response.use(
  <T>(response: AxiosResponse<T>) => {
    return response.data;
  },
  (error) => {
    const { message } = App.useApp();
    const errorMessage = error.response?.data?.message || error.message || '请求失败';
    message.error(errorMessage);
    return Promise.reject(error);
  }
);

export const request = <T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> => {
  return _request(config).then((response: AxiosResponse) => {
    return response as unknown as ApiResponse<T>;
  });
};

export default _request;