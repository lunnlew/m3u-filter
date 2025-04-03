import { ApiResponse } from '@/types/api';
import request from '@/utils/request';

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

export const fetchBlockedDomains = async (
  page: number = 1, 
  pageSize: number = 10,
  keyword?: string
): Promise<BlockedDomainsResponse> => {
  const response = await request<ApiResponse<BlockedDomainsResponse>>({
    method: 'get',
    url: '/blocked-domains',
    params: {
      page,
      page_size: pageSize,
      keyword
    }
  });
  return response.data.data;
};

export const removeBlockedDomain = async (domain: string): Promise<void> => {
  await request<ApiResponse<void>>({
    method: 'delete',
    url: `/blocked-domains/${domain}`
  });
};