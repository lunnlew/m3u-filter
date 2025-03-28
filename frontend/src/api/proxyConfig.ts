import { request } from '../utils/request';
import type { ProxyConfig } from '../types/proxy';

export const fetchProxyConfig = async (): Promise<ProxyConfig> => {
  const response = await request<ProxyConfig>({
    method: 'get',
    url: '/proxy-config'
  });
  return response.data;
};

export const updateProxyConfig = async (config: ProxyConfig): Promise<void> => {
  const response = await request<void>({
    method: 'put',
    url: '/proxy-config',
    data: config
  });
  return response.data;
};