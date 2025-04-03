import request from '@/utils/request';
import type { SiteConfig } from '../types/site';
import { ApiResponse } from '@/types/api';

export const fetchSiteConfig = async (): Promise<SiteConfig> => {
  const response = await request<ApiResponse<SiteConfig>>({
    method: 'get',
    url: '/site-config'
  });
  return response.data.data;
};