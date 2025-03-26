import axios, { AxiosResponse } from 'axios';
import { message } from 'antd';

export interface ApiResponse<T = any> {
  data: T;
  message: string;
  code: number;
}

const request = axios.create({
  baseURL: 'http://localhost:3232/api',
  timeout: 30000,
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data;
  },
  (error) => {
    const errorMessage = error.response?.data?.message || error.message || '请求失败';
    message.error(errorMessage);
    return Promise.reject(error);
  }
);

export default request;