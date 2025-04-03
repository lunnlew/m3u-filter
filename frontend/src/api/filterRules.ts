import request from '@/utils/request';
import type { FilterRule, GenerateM3UResponse } from '../types/filter';
import { ApiResponse } from '@/types/api';

export const fetchFilterRules = async (params?: { keyword?: string; type?: string }): Promise<FilterRule[]> => {
  const response = await request<ApiResponse<FilterRule[]>>({
    method: 'get',
    url: '/filter-rules',
    params
  });
  return response.data.data;
};

export const createOrUpdateFilterRule = async (values: FilterRule): Promise<FilterRule> => {
  const response = await request<ApiResponse<FilterRule>>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/filter-rules/${values.id}` : '/filter-rules',
    data: values
  });
  return response.data.data;
};

export const deleteFilterRule = async (id: number): Promise<ApiResponse> => {
  const response = await request<ApiResponse>({
    method: 'delete',
    url: `/filter-rules/${id}`
  });
  return response.data;
};

export const toggleFilterRule = async (rule: FilterRule): Promise<ApiResponse<FilterRule>> => {
  const response = await request<ApiResponse<FilterRule>>({
    method: 'put',
    url: `/filter-rules/${rule.id}`,
    data: { ...rule, enabled: !rule.enabled }
  });
  return response.data;
};

export const applyFilterRules = async (channels: any[]): Promise<FilterRule> => {
  const response = await request<ApiResponse<FilterRule>>({
    method: 'post',
    url: '/filter-rules/apply',
    data: { channels }
  });
  return response.data.data;
};

export const generateM3U = async (channels: any[]): Promise<ApiResponse> => {
  const response = await request<ApiResponse<ApiResponse>>({
    method: 'post',
    url: '/filter-rules/generate-m3u',
    data: { channels }
  });
  return response.data;
};