import { request } from '../utils/request';
import type { SiteConfig } from '../types/site';

export const fetchSiteConfig = async (): Promise<SiteConfig> => {
  const response = await request<SiteConfig>({
    method: 'get',
    url: '/site-config'
  });
  return response.data;
};