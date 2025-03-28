import { useQuery } from '@tanstack/react-query';
import { fetchSiteConfig } from '../api/siteConfig';
import type { SiteConfig } from '../types/site';

export const useSiteConfig = () => {
  return useQuery<SiteConfig>({
    queryKey: ['siteConfig'],
    queryFn: fetchSiteConfig,
  });
};