import { request } from '../utils/request';

export interface BlockedDomain {
  domain: string;
  failure_count: number;
  last_failure_time: string;
  created_at: string;
  updated_at: string;
}

export interface BlockedDomainsResponse {
  items: BlockedDomain[];
  total: number;
  page: number;
  page_size: number;
}

export const fetchBlockedDomains = async (page: number = 1, pageSize: number = 10): Promise<BlockedDomainsResponse> => {
  const response = await request<BlockedDomainsResponse>({
    method: 'get',
    url: '/blocked-domains',
    params: {
      page,
      page_size: pageSize
    }
  });
  return response.data;
};

export const removeBlockedDomain = async (domain: string): Promise<void> => {
  const response = await request<void>({
    method: 'delete',
    url: `/blocked-domains/${domain}`
  });
  return response.data;
};