import { request } from '../utils/request';
import type { EPGChannel } from '../types/epg';
import { ApiResponse } from '@/types/api';
import { GenerateEPGResponse } from '@/hooks/epgChannels';

import { EPGChannelFilters } from '../hooks/epgChannels';

export const fetchEPGChannels = async (filters?: EPGChannelFilters): Promise<EPGChannel[]> => {
  // 构建查询参数
  const params: Record<string, string> = {};
  if (filters) {
    if (filters.channel_id) params.channel_id = filters.channel_id;
    if (filters.source_name) params.source_name = filters.source_name;
    if (filters.category) params.category = filters.category;
  }

  const response = await request<EPGChannel[]>({
    method: 'get',
    url: '/epg-channels',
    params
  });
  return response.data;
};

export const createOrUpdateEPGChannel = async (values: EPGChannel): Promise<ApiResponse<EPGChannel>> => {
  const response = await request<ApiResponse<EPGChannel>>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/epg-channels/${values.id}` : '/epg-channels',
    data: values
  });
  return response.data;
};

export const deleteEPGChannel = async (id: number): Promise<ApiResponse<EPGChannel>> => {
  const response = await request<ApiResponse<EPGChannel>>({
    method: 'delete',
    url: `/epg-channels/${id}`
  });
  return response.data;
};

export const clearAllEPGChannels = async (): Promise<ApiResponse<EPGChannel>> => {
  const response = await request<ApiResponse<EPGChannel>>({
    method: 'delete',
    url: '/epg-channels-clear-all'
  });
  return response.data;
};

export const generateEPGXML = async (): Promise<GenerateEPGResponse> => {
  const response = await request<GenerateEPGResponse>({
    method: 'post',
    url: '/epg-channels/export-xml'
  });
  return response.data;
};