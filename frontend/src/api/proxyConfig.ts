import request from '@/utils/request';
import type { ProxyConfig } from '../types/proxy';
import { ApiResponse } from '@/types/api';

export const fetchProxyConfig = async (): Promise<ProxyConfig> => {
  const response = await request<ApiResponse<ProxyConfig>>({
    method: 'get',
    url: '/proxy-config'
  });
  return response.data.data;
};

export const updateProxyConfig = async (config: ProxyConfig): Promise<void> => {
  const response = await request<ApiResponse<void>>({
    method: 'put',
    url: '/proxy-config',
    data: config
  });
  return response.data.data;
};