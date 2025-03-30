import { request } from '../utils/request';
import type { EPGSource } from '../types/epg';
import { ApiResponse } from '@/types/api';

export const fetchEPGSources = async (params?: Record<string, unknown>): Promise<EPGSource[]> => {
  const response = await request<EPGSource[]>({
    method: 'get',
    url: '/epg-sources',
    params
  });
  return response.data;
};

export const createOrUpdateEPGSource = async (values: EPGSource): Promise<ApiResponse<EPGSource>> => {
  const response = await request<EPGSource>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/epg-sources/${values.id}` : '/epg-sources',
    data: values
  });
  return response;
};

export const deleteEPGSource = async (id: number): Promise<void> => {
  const response = await request<void>({
    method: 'delete',
    url: `/epg-sources/${id}`
  });
  return response.data;
};

export const syncEPGSource = async (id: number): Promise<ApiResponse> => {
  const response = await request<ApiResponse>({
    method: 'post',
    url: `/epg-sources/${id}/sync`
  });
  return response;
};