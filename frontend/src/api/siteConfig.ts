import { useQuery } from '@tanstack/react-query';
import request, { ApiResponse } from '../utils/request';

export interface SiteConfig {
  base_url: string;
  static_url_prefix: string;
}

// 获取站点配置
export const useSiteConfig = () => {
  return useQuery<SiteConfig>({
    queryKey: ['siteConfig'],
    queryFn: () => request.get('/site-config').then((res) => res.data),
  });
};